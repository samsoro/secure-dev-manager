"""
Windows Safety Manager - ENHANCED VERSION
Provides comprehensive Windows-specific process safety checks
Blocks both direct and indirect attempts to kill MCP servers
Uses generic error messages to prevent circumvention
"""

import os
import sys
import subprocess
import psutil
from typing import Dict, List, Optional, Set
from pathlib import Path

class WindowsSafetyManager:
    """
    Manages Windows-specific safety rules for process operations
    Primary goal: Prevent ANY termination of MCP servers (direct or indirect)
    """
    
    def __init__(self):
        self.is_windows = sys.platform == 'win32'
        
        # MCP-related patterns to protect (kept private)
        self._mcp_patterns = [
            'mcp',
            'secure_mcp',
            'mcp-infrastructure',
            'api-toolbox',
            'claude-mcp',
            'mcp_server',
            'mcp-server'
        ]
        
        # Claude Desktop related patterns (kept private)
        self._claude_patterns = [
            'Claude',
            'claude-desktop',
            'Anthropic'
        ]
        
        # Critical system processes to protect
        self._system_protected = [
            'System',
            'csrss.exe',
            'winlogon.exe',
            'services.exe',
            'lsass.exe',
            'svchost.exe'
        ]
        
        # Processes that MCP servers run on - MUST be protected
        self._runtime_processes = [
            'python.exe',
            'python3.exe',
            'python',
            'node.exe',
            'node',
            'cmd.exe',
            'powershell.exe',
            'pwsh.exe'
        ]
        
        # Dangerous kill commands that should be blocked entirely
        self._dangerous_kill_patterns = [
            'taskkill',
            'kill',
            'pkill',
            'killall',
            'stop-process',
            'terminate',
            'wmic process',
            'get-process'
        ]
        
        # Initialize protected PIDs cache
        self._protected_pids_cache = set()
        self._cache_timestamp = 0
        self.cache_duration = 5  # Refresh cache every 5 seconds
        
        # Public property for backward compatibility
        self.mcp_patterns = self._mcp_patterns
        
    def get_safe_subprocess_flags(self) -> int:
        """
        Get safe subprocess creation flags for Windows
        CRITICAL: Never use CREATE_NEW_PROCESS_GROUP flag
        """
        if not self.is_windows:
            return 0
        
        # Use CREATE_NO_WINDOW to hide console windows for background processes
        # but NEVER use CREATE_NEW_PROCESS_GROUP
        CREATE_NO_WINDOW = 0x08000000
        return CREATE_NO_WINDOW
    
    def is_mcp_process(self, process: psutil.Process) -> bool:
        """
        Check if a process is MCP-related (internal use only)
        """
        try:
            # Check process name
            process_name = process.name().lower()
            for pattern in self._mcp_patterns:
                if pattern.lower() in process_name:
                    return True
            
            # Check process command line
            cmdline = ' '.join(process.cmdline()).lower()
            for pattern in self._mcp_patterns:
                if pattern.lower() in cmdline:
                    return True
            
            # Check process executable path
            try:
                exe_path = process.exe().lower()
                for pattern in self._mcp_patterns:
                    if pattern.lower() in exe_path:
                        return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # Check if it's a Python/Node process running MCP-related scripts
            if any(runtime in process_name for runtime in ['python', 'node']):
                for arg in process.cmdline():
                    arg_lower = arg.lower()
                    for pattern in self._mcp_patterns:
                        if pattern.lower() in arg_lower:
                            return True
            
            return False
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # If we can't access the process, err on the side of caution
            return True
    
    def is_claude_related(self, process: psutil.Process) -> bool:
        """
        Check if a process is Claude Desktop related
        """
        try:
            process_name = process.name()
            cmdline = ' '.join(process.cmdline())
            
            for pattern in self._claude_patterns:
                if pattern.lower() in process_name.lower():
                    return True
                if pattern.lower() in cmdline.lower():
                    return True
            
            return False
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True  # Err on the side of caution
    
    def is_system_critical(self, process: psutil.Process) -> bool:
        """
        Check if a process is system critical
        """
        try:
            process_name = process.name()
            return process_name in self._system_protected
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True
    
    def get_protected_pids(self, refresh: bool = False) -> Set[int]:
        """
        Get a set of all protected process PIDs
        """
        import time
        current_time = time.time()
        
        # Refresh cache if needed
        if refresh or (current_time - self._cache_timestamp) > self.cache_duration:
            self._protected_pids_cache = self._scan_protected_pids()
            self._cache_timestamp = current_time
        
        return self._protected_pids_cache
    
    def _scan_protected_pids(self) -> Set[int]:
        """
        Scan system for all protected PIDs
        """
        protected = set()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (self.is_mcp_process(proc) or 
                    self.is_claude_related(proc) or 
                    self.is_system_critical(proc)):
                    protected.add(proc.pid)
                    
                    # Also protect parent and children
                    try:
                        parent = proc.parent()
                        if parent:
                            protected.add(parent.pid)
                    except:
                        pass
                    
                    try:
                        for child in proc.children(recursive=True):
                            protected.add(child.pid)
                    except:
                        pass
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return protected
    
    def can_kill_process(self, pid: int) -> tuple[bool, str]:
        """
        Check if a process can be safely killed - OPTIMIZED VERSION
        Returns generic error messages to prevent circumvention
        """
        # Handle invalid PIDs
        if pid is None:
            return (False, "Invalid process identifier")
        
        if not isinstance(pid, int) or pid <= 0:
            return (False, "Invalid process identifier")
        
        try:
            # Check if process exists
            if not psutil.pid_exists(pid):
                return (False, "Process not found")
            
            process = psutil.Process(pid)
            
            # Quick check for obviously safe processes (skip expensive checks)
            proc_name_lower = process.name().lower()
            safe_processes = ['chrome', 'firefox', 'edge', 'notepad', 'calculator', 'explorer']
            if any(safe in proc_name_lower for safe in safe_processes):
                # Still do a quick cmdline check to ensure no MCP in args
                try:
                    cmdline = ' '.join(process.cmdline()).lower()
                    if 'mcp' not in cmdline and 'claude' not in cmdline:
                        return (True, "Process can be terminated")
                except:
                    pass
            
            # Check if it's protected (don't reveal why)
            if self.is_mcp_process(process):
                return (False, "This operation is not permitted")
            
            if self.is_claude_related(process):
                return (False, "This operation is not permitted")
            
            if self.is_system_critical(process):
                return (False, "This operation is not permitted")
            
            # Skip the expensive get_protected_pids() call for non-critical processes
            # Only check parent if it's a Python/Node process
            if proc_name_lower in ['python.exe', 'python', 'node.exe', 'node', 'cmd.exe']:
                try:
                    parent = process.parent()
                    if parent:
                        if self.is_mcp_process(parent) or self.is_claude_related(parent):
                            return (False, "This operation is not permitted")
                except:
                    pass
            
            return (True, "Process can be terminated")
            
        except psutil.NoSuchProcess:
            return (False, "Process not found")
        except psutil.AccessDenied:
            return (False, "Access denied")
        except Exception:
            return (False, "Operation failed")
    
    def create_safe_subprocess(self, cmd: List[str], **kwargs) -> subprocess.Popen:
        """
        Create a subprocess with Windows-safe flags
        """
        if self.is_windows:
            # Ensure we use safe flags
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = self.get_safe_subprocess_flags()
            else:
                # Ensure dangerous process group flag (0x200) is not present
                dangerous_flag = 0x00000200
                if kwargs['creationflags'] & dangerous_flag:
                    # Remove the dangerous flag
                    kwargs['creationflags'] &= ~dangerous_flag
        
        return subprocess.Popen(cmd, **kwargs)
    
    def check_if_python_script_with_kills(self, command: str) -> bool:
        """
        Check if command is running a Python script that might contain kill operations
        """
        cmd_parts = command.split()
        if len(cmd_parts) >= 2:
            # Check if it's a Python command
            if cmd_parts[0].lower() in ['python', 'python3', 'py', 'python.exe']:
                script_name = cmd_parts[1]
                # Check if script name suggests process management
                kill_indicators = ['kill', 'terminate', 'stop', 'cleanup', 'restart', 'manage']
                if any(indicator in script_name.lower() for indicator in kill_indicators):
                    return True
                # Also check if file exists and contains kill operations
                if os.path.exists(script_name):
                    try:
                        with open(script_name, 'r') as f:
                            content = f.read()
                        # Check for process termination patterns
                        if any(pattern in content for pattern in 
                               ['terminate()', 'kill()', '.terminate', '.kill', 'taskkill', 
                                'os.kill', 'psutil.Process']):
                            return True
                    except:
                        pass
        return False
    
    def get_developer_guidance(self) -> str:
        """
        Return helpful guidance for developers when their script is blocked
        """
        return """Script contains process termination operations.

For safety, use secure-dev-manager tools directly:
  1. find_process: See what's running and protection status
  2. kill_process: Kill specific PIDs (auto-protects MCP)
  3. server_status: Check what's on your dev ports

Example - Free up port 8000:
  @secure-dev-manager server_status
  (Note the PID on port 8000)
  @secure-dev-manager kill_process [that-PID]

Example - Clean up Python processes:
  @secure-dev-manager find_process python
  (Note PIDs where protected=false)
  @secure-dev-manager kill_process [pid1]
  @secure-dev-manager kill_process [pid2]

This ensures MCP infrastructure remains operational."""
    
    def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate if a command is safe to execute
        Provides developer guidance for blocked scripts
        """
        # Handle None or empty command
        if not command:
            return (True, "")
        
        cmd_lower = command.lower()
        
        # Check if it's a Python script with kill operations
        if self.check_if_python_script_with_kills(command):
            return (False, self.get_developer_guidance())
        
        # Block ANY command that tries to kill processes broadly
        # This includes killing python.exe, node.exe, etc.
        for kill_cmd in self._dangerous_kill_patterns:
            if kill_cmd in cmd_lower:
                # Check if targeting runtime processes (Python, Node, etc.)
                for runtime in self._runtime_processes:
                    if runtime.lower() in cmd_lower:
                        # Generic error - don't reveal what's protected
                        return (False, "This operation is not permitted")
                
                # Check if targeting MCP/Claude directly
                for pattern in self._mcp_patterns + self._claude_patterns:
                    if pattern.lower() in cmd_lower:
                        return (False, "This operation is not permitted")
                
                # Block wildcard kills or process listing + kill combos
                dangerous_wildcards = ['*', 'all', '/im', 'where', 'findstr', '|']
                if any(wild in cmd_lower for wild in dangerous_wildcards):
                    return (False, "This operation is not permitted")
        
        # Block WMI or PowerShell process operations
        if any(danger in cmd_lower for danger in ['wmic process', 'get-process', 'stop-process']):
            if any(runtime in cmd_lower for runtime in self._runtime_processes):
                return (False, "This operation is not permitted")
        
        # Block dangerous system commands
        system_dangers = ['format', 'del /s', 'rm -rf /', 'diskpart', 'bcdedit']
        if any(danger in cmd_lower for danger in system_dangers):
            return (False, "This operation is not permitted")
        
        # Block attempts to stop services
        if 'net stop' in cmd_lower or 'sc stop' in cmd_lower:
            return (False, "This operation is not permitted")
        
        return (True, "")
    
    def get_process_info(self, pid: int) -> Dict[str, any]:
        """
        Get basic process information (limited to prevent info gathering)
        """
        try:
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                # Return limited info only
                return {
                    'pid': pid,
                    'name': proc.name(),
                    'status': proc.status()
                }
            else:
                return {'error': 'Process not found'}
        except:
            return {'error': 'Unable to retrieve information'}
