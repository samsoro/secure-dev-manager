#!/usr/bin/env python3
"""
Secure Development Manager MCP Server
Enhanced version with Windows-specific safety to prevent MCP server kills
Inherits from MCPServer base class for common MCP functionality
FIXED: Added Windows stdin/stdout handling to prevent immediate shutdown
"""

import sys
import os
import json
import asyncio
import traceback
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import base class and our modules
from shared.mcp_base import MCPServer
from windows_safety import WindowsSafetyManager
from process_management import ProcessManager

class SecureDevManager(MCPServer):
    """
    Secure development management server with Windows safety
    Inherits from MCPServer for standard MCP protocol handling
    """
    
    def __init__(self):
        super().__init__("secure-dev-manager")
        self.debug_log("Secure Dev Manager initializing...")
        
        # Initialize Windows safety manager
        self.safety = WindowsSafetyManager()
        self.debug_log(f"Windows safety initialized. Is Windows: {self.safety.is_windows}")
        
        # Initialize process manager with safety
        self.process_manager = ProcessManager(self.safety, self.debug_log)
        self.debug_log("Process manager initialized")
        
        # Track initialization state
        self.initialized = False
        
    @property
    def is_windows(self):
        """Check if we're running on Windows"""
        return self.safety.is_windows
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return server capabilities for MCP"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "secure-dev-manager",
                "version": "1.0.0"
            }
        }
    
    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Return list of available tools"""
        return [
            {
                "name": "execute_command",
                "description": "Execute a whitelisted command",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to execute"
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory (optional)"
                        },
                        "background": {
                            "type": "boolean",
                            "description": "Run in background (for servers)",
                            "default": False
                        }
                    },
                    "required": ["command"],
                    "additionalProperties": False
                }
            },
            {
                "name": "check_ports",
                "description": "Check status of development ports",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "integer",
                            "description": "Specific port to check (optional)"
                        }
                    },
                    "additionalProperties": False
                }
            },
            {
                "name": "find_process",
                "description": "Find processes by name with smart performance defaults",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Process name to search for"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Performance mode: instant (<0.05s), quick (<0.2s), smart (auto), full (everything)",
                            "enum": ["instant", "quick", "smart", "full"]
                        },
                        "include_children": {
                            "type": "boolean",
                            "description": "Include child processes (slower)"
                        },
                        "quick_mode": {
                            "type": "boolean",
                            "description": "Legacy: Use mode='quick' instead"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "kill_process",
                "description": "Kill a process by PID (warns about orphans)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to kill"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force kill the process (SIGKILL instead of SIGTERM)",
                            "default": False
                        },
                        "override": {
                            "type": "boolean",
                            "description": "Override protection for user-spawned processes",
                            "default": False
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Preview what would be killed without actually killing (NEW in v3.2)",
                            "default": False
                        }
                    },
                    "required": ["pid"],
                    "additionalProperties": False
                }
            },
            {
                "name": "kill_process_tree",
                "description": "Kill a process and all its children",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID of parent to kill with all children"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force kill the entire tree",
                            "default": False
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Preview what would be killed without actually killing (NEW in v3.2)",
                            "default": False
                        }
                    },
                    "required": ["pid"],
                    "additionalProperties": False
                }
            },
            {
                "name": "server_status",
                "description": "Get server status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "list_allowed",
                "description": "List allowed commands",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "dev_status",
                "description": "Quick overview: ports, processes, MCP health",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "find_process_by_port",
                "description": "Find which process is using a specific port",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "integer",
                            "description": "Port number to check"
                        }
                    },
                    "required": ["port"],
                    "additionalProperties": False
                }
            },
            {
                "name": "cleanup_user_processes",
                "description": "Clean up all user-spawned processes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirm cleanup (safety check)",
                            "default": False
                        }
                    },
                    "additionalProperties": False
                }
            },
            {
                "name": "kill_all_chrome",
                "description": "Kill all Chrome processes at once",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirm killing all Chrome processes",
                            "default": False
                        }
                    },
                    "additionalProperties": False
                }
            },
            {
                "name": "help",
                "description": "Show help information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            # Command aliases (NEW in v3.2)
            {
                "name": "ps",
                "description": "Alias for find_process - Unix-style process search",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Process name to search for"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Performance mode",
                            "enum": ["instant", "quick", "smart", "full"]
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "kill",
                "description": "Alias for kill_process - Unix-style process termination",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to kill"
                        },
                        "force": {
                            "type": "boolean",
                            "default": False
                        },
                        "dry_run": {
                            "type": "boolean",
                            "default": False
                        }
                    },
                    "required": ["pid"]
                }
            },
            {
                "name": "killall",
                "description": "Alias for kill_process_tree - Kill process and children",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to kill with children"
                        },
                        "force": {
                            "type": "boolean",
                            "default": False
                        },
                        "dry_run": {
                            "type": "boolean",
                            "default": False
                        }
                    },
                    "required": ["pid"]
                }
            },
            {
                "name": "netstat",
                "description": "Alias for check_ports - Check network port status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "integer",
                            "description": "Port to check (optional)"
                        }
                    }
                }
            },
            {
                "name": "status",
                "description": "Alias for dev_status - Quick development status overview",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call requests"""
        # Command aliases mapping (NEW in v3.2)
        command_aliases = {
            'ps': 'find_process',
            'kill': 'kill_process', 
            'killall': 'kill_process_tree',
            'netstat': 'check_ports',
            'status': 'dev_status'
        }
        
        # Apply alias if exists
        original_name = tool_name
        tool_name = command_aliases.get(tool_name, tool_name)
        
        if original_name != tool_name:
            self.debug_log(f"Alias '{original_name}' mapped to '{tool_name}'")
        
        self.debug_log(f"Tool call: {tool_name} with args: {arguments}")
        
        try:
            if tool_name == "execute_command":
                return await self.process_manager.execute_command(
                    arguments.get("command"),
                    arguments.get("cwd"),
                    arguments.get("background", False)
                )
            elif tool_name == "check_ports":
                return await self.process_manager.check_ports(
                    arguments.get("port")
                )
            elif tool_name == "find_process":
                # Support mode parameter for performance optimization
                kwargs = {"name": arguments["name"]}
                
                # Map mode if provided (Phase 1 enhancement)
                if "mode" in arguments:
                    kwargs["mode"] = arguments["mode"]
                
                # Legacy support for quick_mode - map to mode="quick"
                if "quick_mode" in arguments and arguments["quick_mode"]:
                    kwargs["mode"] = "quick"
                
                # Include other optional parameters that actually exist
                if "include_args" in arguments:
                    kwargs["include_args"] = arguments["include_args"]
                if "show_full_cmdline" in arguments:
                    kwargs["show_full_cmdline"] = arguments["show_full_cmdline"]
                
                return await self.process_manager.find_process(**kwargs)
            elif tool_name == "kill_process":
                return await self.process_manager.kill_process(
                    arguments["pid"],
                    arguments.get("force", False),
                    arguments.get("override", False),
                    arguments.get("dry_run", False)  # NEW in v3.2
                )
            elif tool_name == "kill_process_tree":
                return await self.process_manager.kill_process_tree(
                    arguments["pid"],
                    arguments.get("force", False),
                    arguments.get("dry_run", False)  # NEW in v3.2
                )
            elif tool_name == "server_status":
                return await self.process_manager.get_server_status()
            elif tool_name == "list_allowed":
                return await self.process_manager.list_allowed_commands()
            elif tool_name == "dev_status":
                return await self.process_manager.dev_status()
            elif tool_name == "find_process_by_port":
                return await self.process_manager.find_process_by_port(
                    arguments["port"]
                )
            elif tool_name == "cleanup_user_processes":
                return await self.process_manager.cleanup_user_processes(
                    arguments.get("confirm", False)
                )
            elif tool_name == "kill_all_chrome":
                return await self.process_manager.kill_all_chrome(
                    arguments.get("confirm", False)
                )
            elif tool_name == "help":
                return await self.process_manager.help()
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
        except Exception as e:
            self.debug_log(f"Error in tool call: {e}")
            self.debug_log(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }

def main():
    """Main loop for Secure Dev Manager MCP server"""
    server = SecureDevManager()
    server.debug_log("Entering main loop")
    
    # CRITICAL: Set up stdin/stdout with proper buffering for Windows
    if sys.platform == 'win32':
        import msvcrt
        import io
        
        # Set binary mode for stdin/stdout
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        
        # Wrap with text encoding
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', line_buffering=True)
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        
        server.debug_log("Windows stdin/stdout configured")
    
    # Set up the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    server.debug_log("Starting to read from stdin")
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                server.debug_log("EOF received, exiting")
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                method = request.get('method', '')
                params = request.get('params', {})
                request_id = request.get('id')
                
                response = None
                
                if method == 'initialize':
                    response = {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': server.get_capabilities()
                    }
                    
                elif method == 'notifications/initialized':
                    continue  # No response needed
                    
                elif method == 'tools/list':
                    response = {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': {
                            'tools': server.get_tools_list()
                        }
                    }
                    
                elif method == 'tools/call':
                    tool_name = params.get('name')
                    arguments = params.get('arguments', {})
                    
                    # Run async tool call in the event loop
                    result = loop.run_until_complete(
                        server.handle_tool_call(tool_name, arguments)
                    )
                    
                    # Format result as content array (MCP protocol requirement)
                    if isinstance(result, dict):
                        # Always return the full result for rich error messages
                        # Don't simplify errors - preserve developer_message, hints, etc.
                        text = json.dumps(result, indent=2)
                    else:
                        text = str(result)
                    
                    response = {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': {'content': [{'type': 'text', 'text': text}]}
                    }
                    
                else:
                    if request_id is not None:
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'error': {'code': -32601, 'message': f'Method not found: {method}'}
                        }
                
                if response:
                    print(json.dumps(response), flush=True)
                    
            except json.JSONDecodeError as e:
                server.debug_log(f"JSON decode error: {e}")
            except Exception as e:
                server.debug_log(f"Request processing error: {e}")
                if 'request_id' in locals() and request_id is not None:
                    error_response = {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'error': {'code': -32603, 'message': f'Internal error: {str(e)}'}
                    }
                    print(json.dumps(error_response), flush=True)
                    
    except Exception as e:
        server.debug_log(f"Fatal error: {e}")
        server.debug_log(f"Traceback: {traceback.format_exc()}")
    finally:
        loop.close()
        server.debug_file.close()


if __name__ == '__main__':
    try:
        # Check if psutil is installed
        try:
            import psutil
        except ImportError:
            print("Error: psutil is required. Please install it with: pip install psutil", file=sys.stderr)
            sys.exit(1)
        
        main()
    except Exception as e:
        sys.exit(1)
