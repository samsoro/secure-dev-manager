"""
Process Management Module - ENHANCED WITH ORPHAN PREVENTION
Prevents orphaned processes through process tree management
"""

import os
import sys
import asyncio
import subprocess
import psutil
import socket
import json
import time
import re
from typing import Dict, List, Any, Optional, Callable, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
from enum import Enum

# Try to import Windows-specific modules for Job Objects
try:
    import win32job
    import win32process
    import win32api
    import pywintypes
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class QueryMode(Enum):
    """Query modes for different performance needs"""
    INSTANT = "instant"  # <0.05s - PIDs and names only
    QUICK = "quick"      # <0.2s - Basic info, no children  
    SMART = "smart"      # <0.5s - Smart defaults based on type
    FULL = "full"        # <2s - Everything including children

class ProcessManager:
    """
    Process management with integrated Windows safety and orphan prevention
    All operations go through safety checks before execution
    Version 3.2: Added command aliases, dry-run support, and human-readable memory
    """
    
    def __init__(self, safety_manager, debug_log: Callable):
        self.safety = safety_manager
        self.debug_log = debug_log
        
        # Basic allowed commands
        self.basic_commands = {
            'dir', 'ls', 'cat', 'type', 'echo', 'date', 'time',
            'hostname', 'whoami', 'pwd', 'cd', 'python', 'pip',
            'git status', 'git log', 'git diff', 'git branch',
            'node', 'npm list', 'ping', 'nslookup', 'tree'
        }
        
        # Development server commands
        self.dev_commands = {
            'netstat', 'tasklist', 'ps',
            'npm start', 'npm run dev', 'npm run build',
            'python app.py', 'python manage.py runserver',
            'flask run', 'uvicorn', 'gunicorn',
            'tail', 'head', 'grep'
        }
        
        self.allowed_commands = self.basic_commands.union(self.dev_commands)
        
        # Project virtual environments
        self.project_venvs = {
            'portfolio-analysis': r'C:\Users\Bizon\AI-Projects\portfolio-analysis\.venv',
            'trip-builder-pro': r'C:\Users\Bizon\AI-Projects\trip-builder-pro\.venv',
        }
        
        # Track server processes we've started
        self.managed_servers = {}
        
        # Track PIDs of processes spawned by this tool (Phase 2)
        self.user_spawned_pids = set()
        self.wrapper_to_actual = {}  # FIX: Map cmd.exe wrapper PID to actual process PID
        
        # Track Job Objects for clean process tree termination (Windows)
        self.job_handles = {} if HAS_WIN32 else None
        
        # Common development ports
        self.dev_ports = {
            3000: 'React Dev Server',
            5000: 'Flask/WebSocket Server',
            8000: 'Django/FastAPI Server',
            8080: 'Alternative Web Server',
            5173: 'Vite Dev Server',
            4200: 'Angular Dev Server'
        }
        
        # Cache for protection status to avoid repeated expensive checks
        self._protection_cache = {}
        self._cache_timestamp = 0
        self._cache_duration = 10  # Refresh every 10 seconds
        
    def _format_memory(self, memory_mb: float) -> str:
        """Format memory in human-readable units"""
        if memory_mb < 1024:
            return f"{memory_mb:.1f} MB"
        else:
            return f"{memory_mb / 1024:.2f} GB"
        
    def _get_process_tree(self, pid: int) -> List[psutil.Process]:
        """Get all child processes recursively"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            return [parent] + children
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []
    
    def _get_actual_process_pid(self, wrapper_pid: int) -> Optional[int]:
        """
        Get the actual process PID from a cmd.exe wrapper
        Returns the first child process that isn't conhost.exe
        """
        try:
            wrapper = psutil.Process(wrapper_pid)
            for child in wrapper.children():
                if child.name().lower() not in ['conhost.exe', 'cmd.exe']:
                    return child.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
    
    def _track_spawned_process_tree(self, pid: int):
        """Track all PIDs in a spawned process tree"""
        try:
            parent = psutil.Process(pid)
            # Track the parent
            self.user_spawned_pids.add(pid)
            
            # Track all children recursively
            for child in parent.children(recursive=True):
                self.user_spawned_pids.add(child.pid)
                self.debug_log(f"Tracking spawned child PID: {child.pid} ({child.name()})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def _find_processes_on_port(self, port: int) -> List[Dict[str, Any]]:
        """Find ALL processes binding to a port (including children)"""
        processes = []
        seen_pids = set()
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == port and proc.pid not in seen_pids:
                        # Found a process on this port
                        proc_info = {
                            'pid': proc.pid,
                            'name': proc.name(),
                            'type': 'primary'
                        }
                        processes.append(proc_info)
                        seen_pids.add(proc.pid)
                        
                        # Also check its children
                        for child in proc.children(recursive=True):
                            if child.pid not in seen_pids:
                                child_info = {
                                    'pid': child.pid,
                                    'name': child.name(),
                                    'type': 'child',
                                    'parent_pid': proc.pid
                                }
                                processes.append(child_info)
                                seen_pids.add(child.pid)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        
        return processes
    
    def _check_protection_cached(self, pid: int, proc_name: str, cmdline: str) -> bool:
        """
        Check if a process is protected, with caching for performance.
        This ensures ACCURATE protection status while maintaining speed.
        """
        # FIX: User-spawned processes are killable with override, so not "protected"
        if pid in self.user_spawned_pids:
            return False
            
        current_time = time.time()
        
        # Refresh cache if expired
        if current_time - self._cache_timestamp > self._cache_duration:
            self._protection_cache.clear()
            self._cache_timestamp = current_time
        
        # Check cache first
        if pid in self._protection_cache:
            return self._protection_cache[pid]
        
        # QUICK CHECKS FIRST (for obvious cases)
        name_lower = proc_name.lower()
        cmdline_lower = cmdline.lower()
        
        # Obvious MCP/Claude processes - mark protected immediately
        critical_patterns = [
            'mcp-server', 'mcp_server', 'secure_dev', 'api-toolbox',
            'claude.exe', 'anthropic', 'mcp-infrastructure'
        ]
        for pattern in critical_patterns:
            if pattern in name_lower or pattern in cmdline_lower:
                self._protection_cache[pid] = True
                return True
        
        # Obvious safe processes - mark unprotected immediately
        safe_patterns = ['chrome', 'firefox', 'edge', 'notepad', 'calculator']
        definitely_safe = any(safe in name_lower for safe in safe_patterns)
        if definitely_safe and 'mcp' not in cmdline_lower:
            self._protection_cache[pid] = False
            return False
        
        # UNCERTAIN CASES - use full safety check (slower but accurate)
        # This includes Python/Node processes that MIGHT be MCP-related
        if name_lower in ['python.exe', 'python', 'node.exe', 'node', 'cmd.exe']:
            try:
                # Use the real safety check for accuracy
                can_kill, _ = self.safety.can_kill_process(pid)
                is_protected = not can_kill
                self._protection_cache[pid] = is_protected
                return is_protected
            except:
                # If we can't determine, err on the side of caution
                self._protection_cache[pid] = True
                return True
        
        # Default to unprotected for other processes
        self._protection_cache[pid] = False
        return False
    
    def _check_port_async(self, port: int) -> Dict[str, Any]:
        """Check a single port (for parallel execution)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)  # Reduced timeout for faster checks
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is open, find ALL processes using it
                processes_on_port = self._find_processes_on_port(port)
                
                # Primary process info (first one found)
                process_info = None
                if processes_on_port:
                    primary = processes_on_port[0]
                    process_info = {
                        'pid': primary['pid'],
                        'name': primary['name'],
                        'has_children': len(processes_on_port) > 1,
                        'total_processes': len(processes_on_port)
                    }
                
                return {
                    'port': port,
                    'status': 'active',
                    'service': self.dev_ports.get(port, 'Unknown'),
                    'process': process_info,
                    'all_processes': processes_on_port if len(processes_on_port) > 1 else None
                }
            else:
                return {
                    'port': port,
                    'status': 'inactive',
                    'service': self.dev_ports.get(port, 'Unknown')
                }
        except Exception as e:
            return {
                'port': port,
                'status': 'error',
                'error': str(e)
            }
        
    def get_venv_for_cwd(self, cwd: str) -> Optional[str]:
        """Get virtual environment for a working directory"""
        if not cwd:
            cwd = os.getcwd()
        
        cwd_path = Path(cwd).resolve()
        
        # Check if we're in a project with .venv
        venv_path = cwd_path / '.venv'
        if venv_path.exists():
            self.debug_log(f"Found .venv in {cwd_path}")
            return str(venv_path)
        
        # Check known project venvs
        for project_name, venv_path in self.project_venvs.items():
            if project_name in str(cwd_path):
                if Path(venv_path).exists():
                    self.debug_log(f"Using venv for {project_name}")
                    return venv_path
        
        return None
    
    def prepare_command_env(self, cwd: Optional[str] = None) -> Dict[str, str]:
        """Prepare environment with proper venv activation"""
        env = os.environ.copy()
        
        venv_path = self.get_venv_for_cwd(cwd)
        if venv_path:
            if sys.platform == 'win32':
                scripts_path = Path(venv_path) / 'Scripts'
                python_exe = scripts_path / 'python.exe'
            else:
                scripts_path = Path(venv_path) / 'bin'
                python_exe = scripts_path / 'python'
            
            # Update PATH to include venv
            env['PATH'] = f"{scripts_path}{os.pathsep}{env.get('PATH', '')}"
            env['VIRTUAL_ENV'] = venv_path
            
            # Remove PYTHONHOME if it exists
            env.pop('PYTHONHOME', None)
            
            self.debug_log(f"Environment configured with venv: {venv_path}")
        
        return env
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is in the allowed list"""
        cmd_parts = command.split()
        if not cmd_parts:
            return False
        
        base_cmd = cmd_parts[0].lower()
        
        # Check exact matches
        if command.lower() in self.allowed_commands:
            return True
        
        # Check command starts
        for allowed in self.allowed_commands:
            if command.lower().startswith(allowed.lower()):
                return True
        
        # Special handling for kill commands (go through safety)
        if base_cmd in ['taskkill', 'kill', 'pkill']:
            return True  # Will be handled with safety checks
        
        # Check if it's a Python/Node script in the project
        if base_cmd in ['python', 'python3', 'node', 'npm']:
            return True
        
        return False
    
    def _create_job_object_for_process(self, process: subprocess.Popen) -> Optional[Any]:
        """Create a Windows Job Object to manage process tree (if available)"""
        if not HAS_WIN32 or not self.safety.is_windows:
            return None
        
        try:
            # Create a Job Object
            job_name = f"SecureDevJob_{process.pid}_{int(time.time())}"
            job = win32job.CreateJobObject(None, job_name)
            
            # Configure job to kill all processes when handle closes
            extended_info = win32job.QueryInformationJobObject(
                job, win32job.JobObjectExtendedLimitInformation
            )
            extended_info['BasicLimitInformation']['LimitFlags'] |= (
                win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            win32job.SetInformationJobObject(
                job, win32job.JobObjectExtendedLimitInformation, extended_info
            )
            
            # Add process to job
            process_handle = win32api.OpenProcess(
                win32process.PROCESS_SET_QUOTA | win32process.PROCESS_TERMINATE,
                False, process.pid
            )
            win32job.AssignProcessToJobObject(job, process_handle)
            
            self.debug_log(f"Created Job Object for PID {process.pid}")
            return job
            
        except Exception as e:
            self.debug_log(f"Failed to create Job Object: {e}")
            return None
    
    async def execute_command(self, command: str, cwd: Optional[str] = None, 
                             background: bool = False) -> Dict[str, Any]:
        """Execute a command with safety checks, timing, and orphan prevention"""
        start_time = time.time()
        self.debug_log(f"Execute command request: {command}")
        
        # Validate command safety
        is_safe, safety_msg = self.safety.validate_command(command)
        if not is_safe:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": f"Command blocked by safety check: {safety_msg}",
                "elapsed_seconds": elapsed
            }
        
        # Check if command is allowed
        if not self.is_command_allowed(command):
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": f"Command not in allowed list: {command}",
                "allowed_commands": sorted(list(self.allowed_commands)),
                "elapsed_seconds": elapsed
            }
        
        # Prepare environment
        env = self.prepare_command_env(cwd)
        
        # Prepare subprocess arguments with safety
        kwargs = {
            'shell': True,
            'env': env,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True
        }
        
        if cwd:
            kwargs['cwd'] = cwd
        
        # Add Windows-safe creation flags
        if self.safety.is_windows:
            kwargs['creationflags'] = self.safety.get_safe_subprocess_flags()
        
        try:
            if background:
                # Start process in background
                process = self.safety.create_safe_subprocess(command, **kwargs)
                wrapper_pid = process.pid
                
                # FIX: Wait a moment for the actual process to spawn
                time.sleep(0.5)
                
                # Get the actual process PID (not the cmd.exe wrapper)
                actual_pid = self._get_actual_process_pid(wrapper_pid)
                if actual_pid:
                    self.debug_log(f"Wrapper PID: {wrapper_pid}, Actual PID: {actual_pid}")
                    self.wrapper_to_actual[wrapper_pid] = actual_pid
                    # Track both PIDs as user-spawned
                    self._track_spawned_process_tree(wrapper_pid)
                    reporting_pid = actual_pid
                else:
                    # Fallback to wrapper PID if we can't find the actual process
                    self.user_spawned_pids.add(wrapper_pid)
                    reporting_pid = wrapper_pid
                
                # Create Job Object for clean termination (Windows only)
                job_handle = None
                if HAS_WIN32 and self.safety.is_windows:
                    job_handle = self._create_job_object_for_process(process)
                    if job_handle:
                        self.job_handles[process.pid] = job_handle
                
                self.managed_servers[wrapper_pid] = {
                    'command': command,
                    'cwd': cwd,
                    'process': process,
                    'actual_pid': actual_pid,
                    'job_handle': job_handle,
                    'started_at': time.time()
                }
                
                elapsed = time.time() - start_time
                return {
                    "success": True,
                    "pid": reporting_pid,  # FIX: Return the actual process PID
                    "wrapper_pid": wrapper_pid,
                    "message": f"Started in background with PID {reporting_pid}",
                    "orphan_prevention": "Job Object" if job_handle else "Process tracking",
                    "elapsed_seconds": elapsed
                }
            else:
                # Run and wait for completion
                process = self.safety.create_safe_subprocess(command, **kwargs)
                stdout, stderr = process.communicate(timeout=30)
                
                elapsed = time.time() - start_time
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "return_code": process.returncode,
                    "elapsed_seconds": elapsed
                }
                
        except subprocess.TimeoutExpired:
            process.kill()
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": "Command timed out after 30 seconds",
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "elapsed_seconds": elapsed
            }
    
    async def check_ports(self, port: Optional[int] = None) -> Dict[str, Any]:
        """Check status of development ports with PARALLEL execution for speed"""
        start_time = time.time()
        
        ports_to_check = [port] if port else list(self.dev_ports.keys())
        
        # Use ThreadPoolExecutor for parallel port checking
        with ThreadPoolExecutor(max_workers=len(ports_to_check)) as executor:
            # Submit all port checks simultaneously
            futures = [executor.submit(self._check_port_async, p) for p in ports_to_check]
            # Gather results
            results_list = [f.result() for f in futures]
        
        # Convert list to dict
        results = {r['port']: {k: v for k, v in r.items() if k != 'port'} 
                  for r in results_list}
        
        # Add developer hints about orphaned processes
        hints = []
        for port_num, info in results.items():
            if info.get('status') == 'active' and info.get('process'):
                proc = info['process']
                if proc.get('has_children'):
                    hints.append(f"Port {port_num}: {proc['total_processes']} processes (parent + children)")
        
        elapsed = time.time() - start_time
        return {
            "success": True,
            "ports": results,
            "developer_hints": hints if hints else ["All ports clear or single-process only"],
            "elapsed_seconds": elapsed
        }
    
    async def find_process(self, name: str, include_args: bool = False, 
                          show_full_cmdline: bool = False, mode: str = "smart") -> Dict[str, Any]:
        """
        Find processes by name - ENHANCED WITH CHILD PROCESS INFO AND PERFORMANCE MODES
        
        Args:
            name: Process name to search for (minimum 2 characters)
            include_args: Include processes where name appears in arguments (slower)
            show_full_cmdline: Show full command line instead of truncating
            mode: Performance mode - 'instant', 'quick', 'smart', or 'full'
        
        Returns all the info developers need while maintaining safety
        """
        start_time = time.time()
        
        # PERFORMANCE FIX: Prevent overly broad searches
        if len(name) < 2:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": "Search query too short. Please use at least 2 characters.",
                "developer_hint": "Single character searches can match hundreds of processes and cause timeouts.",
                "elapsed_seconds": elapsed
            }
        
        # Warn if search might be too broad
        common_letters = ['e', 'a', 's', 'o', 'i', 'n', 't', 'r']
        if len(name) == 2 and any(c in name.lower() for c in common_letters):
            self.debug_log(f"WARNING: Search '{name}' may return many results and be slow")
        
        found_processes = []
        debug_info = {
            'total_scanned': 0,
            'matches_found': 0,
            'protection_checks': 0,
            'cache_hits': 0,
            'processes_with_children': 0
        }
        
        # Get basic info ONLY - no memory_info in the iterator!
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            debug_info['total_scanned'] += 1
            
            try:
                proc_info = proc.info
                proc_name = proc_info.get('name', '')
                cmdline_list = proc_info.get('cmdline', [])
                cmdline = ' '.join(cmdline_list) if cmdline_list else ''
                
                # Check if name matches
                name_lower = name.lower()
                if name_lower in proc_name.lower():
                    match = True
                elif include_args and cmdline and name_lower in cmdline.lower():
                    match = True
                else:
                    match = False
                
                if match:
                    debug_info['matches_found'] += 1
                    
                    # Mode-based optimization: Skip children check in instant/quick modes
                    children = []
                    if mode not in ["instant", "quick"]:
                        try:
                            child_procs = proc.children(recursive=False)
                            if child_procs:
                                debug_info['processes_with_children'] += 1
                                children = [
                                    {'pid': c.pid, 'name': c.name()}
                                    for c in child_procs[:5]  # Limit to first 5 for brevity
                                ]
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # Check protection status (with caching)
                    debug_info['protection_checks'] += 1
                    if proc.pid in self._protection_cache:
                        debug_info['cache_hits'] += 1
                    
                    is_protected = self._check_protection_cached(
                        proc.pid, proc_name, cmdline
                    )
                    
                    # Mode-based optimization: Skip expensive operations in instant mode
                    if mode == "instant":
                        # Instant mode: Skip memory, CPU, threads, creation time
                        memory_mb = 0
                        cpu_percent = 0
                        threads = 0
                        created = "N/A (instant mode)"
                    else:
                        # Get detailed info for quick/smart/full modes
                        try:
                            memory_info = proc.memory_info()
                            memory_mb = memory_info.rss / (1024 * 1024)
                            
                            # Skip CPU percent in quick mode (it's the slowest operation)
                            if mode == "quick":
                                cpu_percent = 0
                            else:
                                cpu_percent = proc.cpu_percent()  # FIXED: Removed blocking interval for 2-7x speedup
                            
                            threads = proc.num_threads()
                            create_time = proc.create_time()
                            created = time.strftime('%Y-%m-%d %H:%M:%S', 
                                                   time.localtime(create_time))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            memory_mb = 0
                            cpu_percent = 0
                            threads = 0
                            created = "Unknown"
                    
                    # Mode-based optimization: Limit cmdline in instant mode
                    if mode == "instant":
                        # Instant mode: Very short cmdline
                        if len(cmdline) > 50:
                            display_cmdline = cmdline[:50] + "..."
                            truncated = True
                        else:
                            display_cmdline = cmdline
                            truncated = False
                    else:
                        # Normal cmdline handling for other modes
                        if not show_full_cmdline and len(cmdline) > 100:
                            display_cmdline = cmdline[:100] + "..."
                            truncated = True
                        else:
                            display_cmdline = cmdline
                            truncated = False
                    
                    # Add process type detection
                    if 'mcp' in proc_name.lower() or 'mcp' in cmdline.lower():
                        process_type = "MCP Infrastructure"
                    elif 'claude' in proc_name.lower():
                        process_type = "Claude Desktop"
                    elif proc_name.lower() in ['system', 'csrss.exe', 'winlogon.exe']:
                        process_type = "System Process"
                    elif 'python' in proc_name.lower():
                        if 'manage.py' in cmdline:
                            process_type = "Django Server"
                        elif 'flask' in cmdline:
                            process_type = "Flask Server"
                        else:
                            process_type = "Python Process"
                    elif 'node' in proc_name.lower():
                        process_type = "Node.js Process"
                    else:
                        process_type = "User Process"
                    
                    # Build warning if protected
                    warning = None
                    if is_protected:
                        if 'mcp' in proc_name.lower() or 'mcp' in cmdline.lower():
                            warning = "MCP infrastructure - DO NOT KILL"
                        elif 'claude' in proc_name.lower():
                            warning = "Claude Desktop process"
                        else:
                            warning = "Protected process"
                    
                    process_data = {
                        'pid': proc.pid,
                        'name': proc_name,
                        'cmdline': display_cmdline,
                        'cmdline_truncated': truncated,
                        'memory_mb': round(memory_mb, 1),
                        'memory_human': self._format_memory(memory_mb),  # NEW in v3.2
                        'cpu_percent': round(cpu_percent, 1),
                        'threads': threads,
                        'created': created,
                        'protected': is_protected,
                        'warning': warning,
                        'type': process_type,
                        'children_count': len(children),
                        'children': children if children else None
                    }
                    
                    found_processes.append(process_data)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                # Process disappeared or access denied
                continue
            except Exception as e:
                self.debug_log(f"Error processing process: {e}")
                continue
        
        # Sort by PID for consistency
        found_processes.sort(key=lambda x: x['pid'])
        
        elapsed = time.time() - start_time
        
        # Add mode info to response
        mode_description = {
            "instant": "Ultra-fast mode (minimal info)",
            "quick": "Quick mode (no CPU%, no children)",
            "smart": "Balanced mode (auto-optimized)",
            "full": "Complete mode (all details)"
        }
        
        return {
            "success": True,
            "processes": found_processes,
            "count": len(found_processes),
            "elapsed_seconds": elapsed,
            "search_params": {
                "query": name,
                "include_args": include_args,
                "show_full_cmdline": show_full_cmdline,
                "mode": mode,
                "mode_description": mode_description.get(mode, "Unknown mode")
            },
            "debug_info": debug_info
        }
    
    async def kill_process_tree(self, pid: int, force: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """Kill a process and ALL its children - no orphans!
        
        Args:
            pid: Process ID to kill
            force: Use SIGKILL instead of SIGTERM
            dry_run: Preview what would be killed without actually killing (NEW in v3.2)
        """
        start_time = time.time()
        self.debug_log(f"Kill process tree request: PID {pid}, force={force}")
        
        # Validate PID first
        if not pid or pid <= 0:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": "Invalid PID provided",
                "elapsed_seconds": elapsed
            }
        
        # Check if process exists
        if not psutil.pid_exists(pid):
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": f"Process {pid} not found",
                "elapsed_seconds": elapsed
            }
        
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            # FIX: Check if it's user-spawned BEFORE safety check
            is_user_spawned = pid in self.user_spawned_pids
            
            if not is_user_spawned:
                # Only do safety check for non-user-spawned processes
                can_kill, reason = self.safety.can_kill_process(pid)
                if not can_kill:
                    elapsed = time.time() - start_time
                    return {
                        "success": False,
                        "error": f"Cannot kill protected process tree",
                        "reason": reason,
                        "protected": True,
                        "elapsed_seconds": elapsed
                    }
            
            # Get all processes in the tree
            process_tree = self._get_process_tree(pid)
            tree_info = [
                {'pid': p.pid, 'name': p.name()}
                for p in process_tree
            ]
            
            # Dry run - just show what would be killed
            if dry_run:
                elapsed = time.time() - start_time
                return {
                    "success": True,
                    "dry_run": True,
                    "message": "DRY RUN - Would kill the following processes:",
                    "would_kill": tree_info,
                    "process_count": len(tree_info),
                    "method": "Job Object" if (HAS_WIN32 and pid in self.job_handles) else "Manual tree termination",
                    "elapsed_seconds": elapsed
                }
            
            # If we have a Job Object, use it (cleanest method)
            if HAS_WIN32 and pid in self.job_handles:
                try:
                    win32job.TerminateJobObject(self.job_handles[pid], 0)
                    del self.job_handles[pid]
                    
                    # Clean up managed servers
                    if pid in self.managed_servers:
                        del self.managed_servers[pid]
                    
                    elapsed = time.time() - start_time
                    return {
                        "success": True,
                        "message": f"Process tree terminated via Job Object",
                        "method": "Job Object termination",
                        "processes_killed": len(tree_info),
                        "tree": tree_info,
                        "elapsed_seconds": elapsed
                    }
                except Exception as e:
                    self.debug_log(f"Job Object termination failed: {e}")
                    # Fall through to manual method
            
            # Manual tree termination (fallback)
            killed_count = 0
            failed_pids = []
            
            # Kill children first (bottom-up to prevent orphans)
            for proc in reversed(process_tree):
                try:
                    if proc.pid != pid:  # Kill children first
                        if force:
                            proc.kill()
                        else:
                            proc.terminate()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    failed_pids.append(proc.pid)
            
            # Finally kill the parent
            try:
                if force:
                    process.kill()
                else:
                    process.terminate()
                killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                failed_pids.append(pid)
            
            # Clean up managed servers
            if pid in self.managed_servers:
                del self.managed_servers[pid]
            
            # Clean up user_spawned_pids for all killed processes (Phase 2)
            for proc_info in tree_info:
                self.user_spawned_pids.discard(proc_info['pid'])
            
            elapsed = time.time() - start_time
            
            if failed_pids:
                return {
                    "success": False,
                    "message": f"Partial tree termination",
                    "killed": killed_count,
                    "failed": failed_pids,
                    "tree": tree_info,
                    "elapsed_seconds": elapsed
                }
            else:
                return {
                    "success": True,
                    "message": f"Process tree terminated successfully",
                    "method": "Manual tree termination",
                    "processes_killed": killed_count,
                    "tree": tree_info,
                    "elapsed_seconds": elapsed
                }
                
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "elapsed_seconds": elapsed
            }
    
    async def kill_process(self, pid: int, force: bool = False, override: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """
        Kill a process by PID - ENHANCED with orphan warnings and override support
        
        Args:
            pid: Process ID to kill
            force: Use SIGKILL instead of SIGTERM
            override: Override protection for user-spawned processes (Phase 2)
            dry_run: Preview what would be killed without actually killing (NEW in v3.2)
        
        Returns detailed information about the operation
        """
        start_time = time.time()
        self.debug_log(f"Kill process request: PID {pid}, force={force}")
        
        # Validate PID first
        if not pid or pid <= 0:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": "Invalid PID provided",
                "developer_hint": "Use 'find_process' to get valid PIDs",
                "protected": False,
                "elapsed_seconds": elapsed
            }
        
        # Get process info for better error messages
        try:
            if not psutil.pid_exists(pid):
                elapsed = time.time() - start_time
                return {
                    "success": False,
                    "error": f"Process {pid} not found",
                    "developer_hint": "Process may have already terminated",
                    "protected": False,
                    "elapsed_seconds": elapsed
                }
            
            process = psutil.Process(pid)
            process_name = process.name()
            cmdline = ' '.join(process.cmdline())[:100]
            
            # Check for child processes
            children = []
            try:
                child_procs = process.children(recursive=True)
                if child_procs:
                    children = [
                        {'pid': c.pid, 'name': c.name()}
                        for c in child_procs
                    ]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
        except:
            process_name = "Unknown"
            cmdline = ""
            children = []
        
        # Phase 2: Check if this is a user-spawned process
        is_user_spawned = pid in self.user_spawned_pids
        
        if is_user_spawned and not override:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": "Process was spawned by this tool",
                "process_info": {
                    "pid": pid,
                    "name": process_name,
                    "cmdline": cmdline
                },
                "suggestion": "Use override=True to force termination of user-spawned process",
                "developer_hint": "This process was started by execute_command. Use override parameter to kill it.",
                "protected": False,
                "user_spawned": True,
                "elapsed_seconds": elapsed
            }
        
        # Check if process can be killed (skip if override is True for user-spawned)
        if is_user_spawned and override:
            # User explicitly wants to kill their own spawned process
            can_kill = True
            reason = "User-spawned process with override"
        else:
            # Normal safety check
            can_kill, reason = self.safety.can_kill_process(pid)
        
        if not can_kill:
            self.debug_log(f"Process {pid} protected: {reason}")
            elapsed = time.time() - start_time
            
            # Provide developer-friendly explanation
            if 'mcp' in process_name.lower() or 'mcp' in cmdline.lower():
                developer_message = (
                    f"Process {pid} ({process_name}) is part of MCP infrastructure.\n"
                    "Killing this would break your Claude Desktop connection.\n\n"
                    "If you need to restart MCP servers:\n"
                    "1. Close Claude Desktop properly\n"
                    "2. Make your changes\n"
                    "3. Restart Claude Desktop"
                )
            elif 'claude' in process_name.lower():
                developer_message = (
                    f"Process {pid} ({process_name}) is Claude Desktop itself.\n"
                    "Use the application's close button instead."
                )
            else:
                developer_message = (
                    f"Process {pid} ({process_name}) is protected.\n"
                    "Reason: {reason}\n\n"
                    "To see which processes you can safely kill:\n"
                    "@secure-dev-manager find_process [name]\n"
                    "Look for processes where 'protected': false"
                )
            
            return {
                "success": False,
                "error": f"Cannot kill protected process",
                "process_info": {
                    "pid": pid,
                    "name": process_name,
                    "cmdline": cmdline
                },
                "developer_message": developer_message,
                "protected": True,
                "elapsed_seconds": elapsed
            }
        
        # Warn about orphaned processes
        if children:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": "Process has child processes",
                "warning": f"Killing this process would orphan {len(children)} child process(es)",
                "children": children,
                "suggestion": "Use 'kill_process_tree' to terminate the entire process tree",
                "developer_hint": "Orphaned processes can keep ports bound and require system restart",
                "protected": False,
                "elapsed_seconds": elapsed
            }
        
        # Dry run - show what would happen
        if dry_run:
            elapsed = time.time() - start_time
            return {
                "success": True,
                "dry_run": True,
                "message": f"DRY RUN - Would kill process {process_name} (PID {pid})",
                "process_info": {
                    "pid": pid,
                    "name": process_name,
                    "cmdline": cmdline,
                    "children": children
                },
                "method": "SIGKILL" if force else "SIGTERM",
                "elapsed_seconds": elapsed
            }
        
        # Process is safe to kill and has no children - proceed
        try:
            # Final safety check
            if self.safety.is_mcp_process(process):
                self.debug_log(f"SAFETY: Process {pid} detected as MCP in final check")
                elapsed = time.time() - start_time
                return {
                    "success": False,
                    "error": f"Process {pid} ({process_name}) is MCP-related",
                    "developer_message": "Safety check prevented killing MCP infrastructure",
                    "protected": True,
                    "elapsed_seconds": elapsed
                }
            
            # Check if it's a managed server with Job Object
            if pid in self.managed_servers and self.managed_servers[pid].get('job_handle'):
                # Use Job Object for clean termination
                if HAS_WIN32:
                    try:
                        job_handle = self.managed_servers[pid]['job_handle']
                        win32job.TerminateJobObject(job_handle, 0)
                        del self.job_handles[pid]
                        del self.managed_servers[pid]
                        
                        elapsed = time.time() - start_time
                        return {
                            "success": True,
                            "message": f"Process {process_name} (PID {pid}) terminated via Job Object",
                            "method": "Job Object (clean)",
                            "protected": False,
                            "elapsed_seconds": elapsed
                        }
                    except Exception as e:
                        self.debug_log(f"Job Object termination failed: {e}")
                        # Fall through to normal termination
            
            # Normal termination
            if force:
                process.kill()  # SIGKILL
                method = "forcefully terminated (SIGKILL)"
            else:
                process.terminate()  # SIGTERM
                method = "gracefully terminated (SIGTERM)"
            
            # Remove from managed servers if present
            if pid in self.managed_servers:
                del self.managed_servers[pid]
            
            # Clean up user_spawned_pids (Phase 2)
            if pid in self.user_spawned_pids:
                self.user_spawned_pids.discard(pid)
            
            elapsed = time.time() - start_time
            return {
                "success": True,
                "message": f"Process {process_name} (PID {pid}) {method}",
                "developer_hint": f"Process was {method}. Use force=True for stubborn processes.",
                "protected": False,
                "user_spawned": is_user_spawned,
                "elapsed_seconds": elapsed
            }
            
        except psutil.NoSuchProcess:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": f"Process {pid} disappeared during termination",
                "developer_hint": "Process terminated by another means",
                "elapsed_seconds": elapsed
            }
        except psutil.AccessDenied:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": f"Access denied to terminate process {pid}",
                "developer_hint": "Try running with administrator privileges or use force=True",
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "developer_hint": "Unexpected error - check process state manually",
                "elapsed_seconds": elapsed
            }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get status of all managed development servers with FAST parallel port checking"""
        start_time = time.time()
        servers = []
        
        # Check managed servers
        for pid, info in list(self.managed_servers.items()):
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    # Check for children
                    children = []
                    try:
                        child_procs = proc.children(recursive=False)
                        children = [{'pid': c.pid, 'name': c.name()} for c in child_procs]
                    except:
                        pass
                    
                    servers.append({
                        'pid': pid,
                        'command': info['command'],
                        'cwd': info.get('cwd'),
                        'status': 'running',
                        'memory_mb': proc.memory_info().rss // (1024 * 1024),
                        'children_count': len(children),
                        'has_job_object': bool(info.get('job_handle')),
                        'uptime_seconds': int(time.time() - info.get('started_at', 0))
                    })
                else:
                    # Process no longer running
                    del self.managed_servers[pid]
            except psutil.NoSuchProcess:
                del self.managed_servers[pid]
        
        # Check common dev ports (parallel for speed)
        port_status = await self.check_ports()
        
        elapsed = time.time() - start_time
        
        # Add developer hints based on what's found
        hints = []
        active_ports = [p for p, info in port_status['ports'].items() 
                       if info['status'] == 'active']
        if active_ports:
            hints.append(f"Active ports: {', '.join(map(str, active_ports))}")
            
            # Check for processes with children on ports
            for port, info in port_status['ports'].items():
                if info.get('process') and info['process'].get('has_children'):
                    hints.append(f"Port {port} has multiple processes - use kill_process_tree for clean shutdown")
        else:
            hints.append("All common dev ports are available")
        
        # Add Job Object status hint
        if HAS_WIN32:
            hints.append("Job Objects available for clean process termination")
        else:
            hints.append("Install pywin32 for enhanced orphan prevention")
        
        return {
            "success": True,
            "managed_servers": servers,
            "port_status": port_status.get('ports', {}),
            "developer_hints": hints,
            "orphan_prevention": "Job Objects" if HAS_WIN32 else "Process tracking",
            "elapsed_seconds": elapsed
        }
    
    async def dev_status(self) -> Dict[str, Any]:
        """Quick developer status overview (Phase 3)"""
        start_time = time.time()
        
        # Check ports
        port_results = await self.check_ports()
        
        # Count user processes
        user_processes = []
        for pid in list(self.user_spawned_pids):
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    user_processes.append({
                        'pid': pid,
                        'name': proc.name(),
                        'memory_mb': round(proc.memory_info().rss / (1024*1024), 1)
                    })
            except:
                self.user_spawned_pids.discard(pid)
        
        # Check MCP health
        mcp_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'mcp' in cmdline.lower() or 'secure_dev' in cmdline:
                    mcp_count += 1
            except:
                pass
        
        return {
            "success": True,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "ports": port_results['ports'],
            "user_processes": user_processes,
            "user_process_count": len(user_processes),
            "mcp_healthy": mcp_count > 0,
            "mcp_server_count": mcp_count,
            "elapsed_seconds": time.time() - start_time
        }
    
    async def dev_status(self) -> Dict[str, Any]:
        """Quick developer status overview (Phase 3)"""
        start_time = time.time()
        
        # Check ports
        port_results = await self.check_ports()
        
        # Count user processes
        user_processes = []
        for pid in list(self.user_spawned_pids):
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    user_processes.append({
                        'pid': pid,
                        'name': proc.name(),
                        'memory_mb': round(proc.memory_info().rss / (1024*1024), 1)
                    })
            except:
                self.user_spawned_pids.discard(pid)
        
        # Check MCP health
        mcp_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'mcp' in cmdline.lower() or 'secure_dev' in cmdline:
                    mcp_count += 1
            except:
                pass
        
        return {
            "success": True,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "ports": port_results['ports'],
            "user_processes": user_processes,
            "user_process_count": len(user_processes),
            "mcp_healthy": mcp_count > 0,
            "mcp_server_count": mcp_count,
            "elapsed_seconds": time.time() - start_time
        }
    
    async def find_process_by_port(self, port: int) -> Dict[str, Any]:
        """Find which process is using a specific port (Phase 3)"""
        start_time = time.time()
        
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    if conn.pid:
                        proc = psutil.Process(conn.pid)
                        return {
                            "success": True,
                            "port": port,
                            "process": {
                                'pid': conn.pid,
                                'name': proc.name(),
                                'cmdline': ' '.join(proc.cmdline())[:200],
                                'user_spawned': conn.pid in self.user_spawned_pids
                            },
                            "elapsed_seconds": time.time() - start_time
                        }
            
            return {
                "success": True,
                "port": port,
                "process": None,
                "message": f"Port {port} is not in use",
                "elapsed_seconds": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_seconds": time.time() - start_time
            }
    
    async def cleanup_user_processes(self, confirm: bool = False) -> Dict[str, Any]:
        """Clean up all user-spawned processes (Phase 3)"""
        start_time = time.time()
        
        if not self.user_spawned_pids:
            return {
                "success": True,
                "message": "No user-spawned processes to clean up",
                "elapsed_seconds": time.time() - start_time
            }
        
        processes_to_kill = []
        for pid in list(self.user_spawned_pids):
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    processes_to_kill.append({
                        'pid': pid,
                        'name': proc.name()
                    })
            except:
                self.user_spawned_pids.discard(pid)
        
        if not confirm:
            return {
                "success": False,
                "message": "Confirmation required",
                "processes_to_kill": processes_to_kill,
                "count": len(processes_to_kill),
                "suggestion": "Use confirm=True to proceed with cleanup",
                "elapsed_seconds": time.time() - start_time
            }
        
        # Kill all processes
        killed = []
        failed = []
        for proc_info in processes_to_kill:
            try:
                # Try to kill the process tree if it has children
                result = await self.kill_process_tree(proc_info['pid'], force=True)
                if result['success']:
                    killed.append(proc_info)
                else:
                    # If tree kill fails, try single process kill
                    result = await self.kill_process(proc_info['pid'], force=True, override=True)
                    if result['success']:
                        killed.append(proc_info)
                    else:
                        failed.append(proc_info)
            except:
                failed.append(proc_info)
        
        self.user_spawned_pids.clear()
        
        return {
            "success": True,
            "killed": killed,
            "failed": failed,
            "total_cleaned": len(killed),
            "elapsed_seconds": time.time() - start_time
        }
    
    async def kill_all_chrome(self, confirm: bool = False) -> Dict[str, Any]:
        """
        NEW: Kill all Chrome processes at once
        Convenience method for a common developer need
        """
        start_time = time.time()
        
        # Find all Chrome processes
        chrome_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.name().lower():
                    chrome_processes.append({
                        'pid': proc.pid,
                        'name': proc.name()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not chrome_processes:
            return {
                "success": True,
                "message": "No Chrome processes found",
                "elapsed_seconds": time.time() - start_time
            }
        
        if not confirm:
            return {
                "success": False,
                "message": f"Found {len(chrome_processes)} Chrome processes",
                "processes": chrome_processes[:10],  # Show first 10
                "total_count": len(chrome_processes),
                "suggestion": "Use confirm=True to kill all Chrome processes",
                "elapsed_seconds": time.time() - start_time
            }
        
        # Kill all Chrome processes
        killed = 0
        failed = 0
        
        for proc_info in chrome_processes:
            try:
                proc = psutil.Process(proc_info['pid'])
                proc.terminate()
                killed += 1
            except:
                failed += 1
        
        return {
            "success": True,
            "message": f"Killed {killed} Chrome processes",
            "killed_count": killed,
            "failed_count": failed,
            "elapsed_seconds": time.time() - start_time
        }
    
    async def help(self) -> Dict[str, Any]:
        """
        NEW: Simple help command alias for list_allowed
        """
        return await self.list_allowed_commands()
    
    async def list_allowed_commands(self) -> Dict[str, Any]:
        """Enhanced version with better organization (Phase 4)"""
        start_time = time.time()
        
        return {
            "success": True,
            "commands": {
                "basic": sorted(list(self.basic_commands)),
                "development": sorted(list(self.dev_commands))
            },
            "tools": {
                "process_management": [
                    "find_process - Search by name (with performance modes)",
                    "find_process_by_port - Find what's using a port",
                    "kill_process - Kill single process (with override)",
                    "kill_process_tree - Kill process and all children",
                    "kill_all_chrome - Kill all Chrome processes (NEW)",
                    "cleanup_user_processes - Clean all spawned processes"
                ],
                "development": [
                    "execute_command - Run whitelisted commands",
                    "check_ports - Check development ports",
                    "dev_status - Quick overview dashboard",
                    "server_status - Managed server details"
                ],
                "info": [
                    "help - Show this help (NEW)",
                    "list_allowed - This command (shows all capabilities)"
                ]
            },
            "performance_modes": {
                "instant": "<0.05s - PIDs and names only",
                "quick": "<0.2s - Basic info, no CPU%",
                "smart": "Auto-optimized (default)",
                "full": "<2s - Everything including children"
            },
            "safety_features": {
                "mcp_protection": "Active - prevents killing MCP infrastructure",
                "orphan_prevention": "Job Objects" if HAS_WIN32 else "Process tracking",
                "user_spawn_tracking": "Active - tracks processes started by this tool"
            },
            "tips": [
                "Use 'mode=instant' for ultra-fast process searches",
                "Use 'override=True' to kill user-spawned processes",
                "Use 'dev_status' for a quick overview of everything",
                "Use 'find_process_by_port' to identify port conflicts",
                "Use 'kill_all_chrome' to quickly free up memory (NEW)"
            ],
            "version": "3.2-alias-update",
            "elapsed_seconds": time.time() - start_time
        }
