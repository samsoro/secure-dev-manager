# API Reference - v3.2

Complete API documentation for the Secure Development Manager MCP Server.

## Table of Contents

1. [Command Aliases](#command-aliases)
2. [execute_command](#execute_command)
3. [find_process / ps](#find_process--ps)
4. [kill_process / kill](#kill_process--kill)
5. [kill_process_tree / killall](#kill_process_tree--killall)
6. [check_ports / netstat](#check_ports--netstat)
7. [dev_status / status](#dev_status--status)
8. [server_status](#server_status)
9. [list_allowed_commands / help](#list_allowed_commands--help)
10. [Additional Tools](#additional-tools)

---

## Command Aliases

**NEW in v3.2**: Use either the full command name or its Unix-style alias.

| Alias | Full Command | Since |
|-------|--------------|-------|
| `ps` | `find_process` | v3.2 |
| `kill` | `kill_process` | v3.2 |
| `killall` | `kill_process_tree` | v3.2 |
| `netstat` | `check_ports` | v3.2 |
| `status` | `dev_status` | v3.2 |
| `help` | `list_allowed_commands` | v3.1 |

---

## execute_command

Execute whitelisted commands with automatic virtual environment support.

### Syntax
```bash
@secure-dev-manager execute_command <command> [--cwd <directory>] [--background]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | string | Yes | The command to execute |
| `cwd` | string | No | Working directory (defaults to current) |
| `background` | boolean | No | Run command in background |

### Returns

```json
{
  "success": true,
  "stdout": "Command output...",
  "stderr": "",
  "return_code": 0,
  "elapsed_seconds": 0.025,
  "pid": 12345,  // For background processes
  "wrapper_pid": 12346,  // Windows cmd.exe wrapper
  "orphan_prevention": "Job Object"  // or "Process tracking"
}
```

### Examples

```bash
# Run in foreground
@secure-dev-manager execute_command "python --version"

# Run in background
@secure-dev-manager execute_command "python app.py" --background

# Run with specific working directory
@secure-dev-manager execute_command "npm install" --cwd "C:/projects/myapp"
```

---

## find_process / ps

Find processes by name with performance optimization modes.

### Syntax
```bash
# Using full command
@secure-dev-manager find_process <name> [--mode <mode>] [--include-args] [--show-full-cmdline]

# Using alias (NEW in v3.2)
@secure-dev-manager ps <name> [--mode <mode>]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Process name to search (min 2 chars) |
| `mode` | string | No | Performance mode: instant/quick/smart/full |
| `include_args` | boolean | No | Search in command arguments |
| `show_full_cmdline` | boolean | No | Show full command line |

### Performance Modes

| Mode | Speed | Information | Use Case |
|------|-------|-------------|----------|
| `instant` | <0.05s | PID, name only | Quick listing |
| `quick` | <0.2s | Basic info, no CPU% | Fast search |
| `smart` | <0.5s | Auto-optimized | Default |
| `full` | <2s | Everything + children | Detailed analysis |

### Returns

```json
{
  "success": true,
  "processes": [
    {
      "pid": 12345,
      "name": "python.exe",
      "cmdline": "python app.py",
      "memory_mb": 1109.4,
      "memory_human": "1.08 GB",  // NEW in v3.2
      "cpu_percent": 2.5,
      "threads": 4,
      "created": "2025-09-06 14:30:00",
      "protected": false,
      "warning": null,
      "type": "Python Process",
      "children_count": 2,
      "children": [
        {"pid": 12346, "name": "node.exe"},
        {"pid": 12347, "name": "ping.exe"}
      ]
    }
  ],
  "count": 1,
  "elapsed_seconds": 0.15
}
```

### Examples

```bash
# Quick search using alias
@secure-dev-manager ps python

# Ultra-fast mode
@secure-dev-manager ps chrome --mode=instant

# Search in arguments
@secure-dev-manager find_process manage.py --include-args

# Full details with children
@secure-dev-manager ps node --mode=full
```

---

## kill_process / kill

Kill a process by PID with safety checks and dry-run support.

### Syntax
```bash
# Using full command
@secure-dev-manager kill_process <pid> [--force] [--override] [--dry-run]

# Using alias (NEW in v3.2)
@secure-dev-manager kill <pid> [--force] [--override] [--dry-run]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pid` | integer | Yes | Process ID to kill |
| `force` | boolean | No | Use SIGKILL instead of SIGTERM |
| `override` | boolean | No | Override user-spawned protection |
| `dry_run` | boolean | No | Preview without killing (NEW in v3.2) |

### Returns

#### Normal Kill
```json
{
  "success": true,
  "message": "Process python.exe (PID 12345) gracefully terminated (SIGTERM)",
  "protected": false,
  "user_spawned": false,
  "elapsed_seconds": 0.014
}
```

#### Dry Run (NEW in v3.2)
```json
{
  "success": true,
  "dry_run": true,
  "message": "DRY RUN - Would kill process python.exe (PID 12345)",
  "process_info": {
    "pid": 12345,
    "name": "python.exe",
    "cmdline": "python app.py",
    "children": []
  },
  "method": "SIGTERM",
  "elapsed_seconds": 0.01
}
```

#### Error Cases
```json
{
  "success": false,
  "error": "Process has child processes",
  "warning": "Killing this process would orphan 3 child process(es)",
  "children": [
    {"pid": 12346, "name": "node.exe"}
  ],
  "suggestion": "Use 'kill_process_tree' to terminate the entire process tree"
}
```

### Examples

```bash
# Preview what would happen (NEW in v3.2)
@secure-dev-manager kill 12345 --dry-run

# Normal termination
@secure-dev-manager kill 12345

# Force kill
@secure-dev-manager kill 12345 --force

# Kill user-spawned process
@secure-dev-manager kill 12345 --override
```

---

## kill_process_tree / killall

Kill a process and all its children to prevent orphans.

### Syntax
```bash
# Using full command
@secure-dev-manager kill_process_tree <pid> [--force] [--dry-run]

# Using alias (NEW in v3.2)
@secure-dev-manager killall <pid> [--force] [--dry-run]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pid` | integer | Yes | Parent process ID |
| `force` | boolean | No | Force kill entire tree |
| `dry_run` | boolean | No | Preview without killing (NEW in v3.2) |

### Returns

#### Normal Kill
```json
{
  "success": true,
  "message": "Process tree terminated successfully",
  "method": "Job Object termination",
  "processes_killed": 4,
  "tree": [
    {"pid": 12345, "name": "python.exe"},
    {"pid": 12346, "name": "node.exe"},
    {"pid": 12347, "name": "ping.exe"}
  ],
  "elapsed_seconds": 0.02
}
```

#### Dry Run (NEW in v3.2)
```json
{
  "success": true,
  "dry_run": true,
  "message": "DRY RUN - Would kill the following processes:",
  "would_kill": [
    {"pid": 12345, "name": "python.exe"},
    {"pid": 12346, "name": "node.exe"}
  ],
  "process_count": 2,
  "method": "Job Object",
  "elapsed_seconds": 0.01
}
```

### Examples

```bash
# Preview process tree termination
@secure-dev-manager killall 12345 --dry-run

# Kill process and all children
@secure-dev-manager killall 12345

# Force kill entire tree
@secure-dev-manager killall 12345 --force
```

---

## check_ports / netstat

Check status of development ports.

### Syntax
```bash
# Using full command
@secure-dev-manager check_ports [port]

# Using alias (NEW in v3.2)
@secure-dev-manager netstat [port]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port` | integer | No | Specific port to check (checks all if omitted) |

### Returns

```json
{
  "success": true,
  "ports": {
    "3000": {
      "status": "active",
      "service": "React Dev Server",
      "process": {
        "pid": 12345,
        "name": "node.exe",
        "has_children": true,
        "total_processes": 3
      }
    },
    "8000": {
      "status": "inactive",
      "service": "Django/FastAPI Server"
    }
  },
  "developer_hints": [
    "Port 3000: 3 processes (parent + children)"
  ],
  "elapsed_seconds": 0.2
}
```

### Examples

```bash
# Check all development ports
@secure-dev-manager netstat

# Check specific port
@secure-dev-manager netstat 8000
```

---

## dev_status / status

Quick overview of development environment.

### Syntax
```bash
# Using full command
@secure-dev-manager dev_status

# Using alias (NEW in v3.2)
@secure-dev-manager status
```

### Returns

```json
{
  "success": true,
  "timestamp": "2025-09-06 14:39:13",
  "ports": {
    "3000": {"status": "inactive", "service": "React Dev Server"},
    "8000": {"status": "active", "service": "Django/FastAPI Server"}
  },
  "user_processes": [
    {"pid": 12345, "name": "python.exe", "memory_mb": 45.2}
  ],
  "user_process_count": 1,
  "mcp_healthy": true,
  "mcp_server_count": 6,
  "elapsed_seconds": 0.23
}
```

---

## server_status

Get detailed status of managed servers.

### Syntax
```bash
@secure-dev-manager server_status
```

### Returns

```json
{
  "success": true,
  "managed_servers": [
    {
      "pid": 12345,
      "command": "python app.py",
      "cwd": "C:/projects/myapp",
      "status": "running",
      "memory_mb": 145,
      "children_count": 2,
      "has_job_object": true,
      "uptime_seconds": 3600
    }
  ],
  "port_status": {
    "3000": {"status": "active"},
    "8000": {"status": "inactive"}
  },
  "developer_hints": [
    "Port 3000 has multiple processes - use kill_process_tree for clean shutdown"
  ],
  "orphan_prevention": "Job Objects",
  "elapsed_seconds": 0.15
}
```

---

## list_allowed_commands / help

List all allowed commands and capabilities.

### Syntax
```bash
# Using full command
@secure-dev-manager list_allowed_commands

# Using alias
@secure-dev-manager help
```

### Returns

```json
{
  "success": true,
  "commands": {
    "basic": ["cat", "cd", "date", "dir", "echo", "git status", "python"],
    "development": ["npm start", "flask run", "uvicorn", "gunicorn"]
  },
  "tools": {
    "process_management": [
      "find_process - Search by name (with performance modes)",
      "kill_process - Kill single process (with override)",
      "kill_process_tree - Kill process and all children"
    ]
  },
  "performance_modes": {
    "instant": "<0.05s - PIDs and names only",
    "quick": "<0.2s - Basic info, no CPU%",
    "smart": "Auto-optimized (default)",
    "full": "<2s - Everything including children"
  },
  "safety_features": {
    "mcp_protection": "Active",
    "orphan_prevention": "Job Objects",
    "user_spawn_tracking": "Active"
  },
  "version": "3.2-alias-update",
  "elapsed_seconds": 0.001
}
```

---

## Additional Tools

### find_process_by_port

Find which process is using a specific port.

```bash
@secure-dev-manager find_process_by_port 8000
```

### cleanup_user_processes

Clean up all processes started by this tool.

```bash
@secure-dev-manager cleanup_user_processes --confirm
```

### kill_all_chrome

Kill all Chrome processes at once.

```bash
@secure-dev-manager kill_all_chrome --confirm
```

---

## Error Handling

All tools return consistent error structures:

```json
{
  "success": false,
  "error": "Error message",
  "suggestion": "How to fix it",
  "developer_hint": "Additional context",
  "elapsed_seconds": 0.01
}
```

## Safety Features

### MCP Protection
- Processes identified as MCP infrastructure cannot be killed
- Shows warning: "MCP infrastructure - DO NOT KILL"

### User-Spawned Protection
- Processes started by execute_command are tracked
- Require `--override` to kill

### Orphan Prevention
- Warns when killing would create orphaned processes
- Suggests using kill_process_tree instead

## Version History

- **v3.2**: Added command aliases, dry-run support, human-readable memory
- **v3.1**: Added override parameter, improved error messages
- **v3.0**: Added performance modes, orphan prevention
