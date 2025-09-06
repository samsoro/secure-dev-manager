# Quick Reference - Secure Dev Manager v3.2

## Command Aliases (NEW in v3.2)

Use familiar Unix-style commands or traditional names - both work!

| Alias | Full Command | Description |
|-------|--------------|-------------|
| `ps` | `find_process` | Search for processes |
| `kill` | `kill_process` | Kill single process |
| `killall` | `kill_process_tree` | Kill process and children |
| `netstat` | `check_ports` | Check network ports |
| `status` | `dev_status` | Quick overview |

## Common Commands

### Finding Processes
```bash
# Quick process search (Unix-style)
@secure-dev-manager ps python
@secure-dev-manager ps chrome
@secure-dev-manager ps node

# With performance modes
@secure-dev-manager ps python --mode=instant   # <0.05s, minimal info
@secure-dev-manager ps python --mode=quick     # <0.2s, no CPU%
@secure-dev-manager ps python --mode=smart     # Auto-optimized (default)
@secure-dev-manager ps python --mode=full      # All details + children
```

### Checking Ports
```bash
# Check all development ports
@secure-dev-manager netstat

# Check specific port
@secure-dev-manager netstat 8000
@secure-dev-manager netstat 3000
```

### Killing Processes (with Dry-Run)
```bash
# Preview what would be killed (NEW in v3.2)
@secure-dev-manager kill 12345 --dry-run
@secure-dev-manager killall 12345 --dry-run

# Actually kill processes
@secure-dev-manager kill 12345              # Single process
@secure-dev-manager kill 12345 --force      # Force kill (SIGKILL)
@secure-dev-manager killall 12345           # Process + all children
```

### Managing User-Spawned Processes
```bash
# Start a background process
@secure-dev-manager execute_command "python server.py" --background

# Kill your own spawned process
@secure-dev-manager kill [PID] --override

# Clean up all user processes
@secure-dev-manager cleanup_user_processes --confirm
```

### Quick Status
```bash
# Development environment overview
@secure-dev-manager status

# Detailed server status
@secure-dev-manager server_status

# List all available commands
@secure-dev-manager help
@secure-dev-manager list_allowed
```

## Performance Modes

| Mode | Speed | Info Level | Use Case |
|------|-------|------------|----------|
| `instant` | <0.05s | PID & name only | Quick checks |
| `quick` | <0.2s | No CPU%, no children | Fast listing |
| `smart` | <0.5s | Auto-optimized | Default, balanced |
| `full` | <2s | Everything | Detailed analysis |

## Safety Features

### 🛡️ Protected Processes
- MCP infrastructure processes are **protected**
- Shows warning: "MCP infrastructure - DO NOT KILL"
- Cannot be killed even with --force

### 🔒 User-Spawned Protection
- Processes you start are tracked
- Requires `--override` to kill
- Prevents accidental termination

### 👶 Orphan Prevention
- Warns when killing would create orphans
- Use `killall` to kill entire process tree
- No more stuck ports!

## Memory Display (NEW in v3.2)

Processes now show human-readable memory:
- `memory_mb`: 1109.4 (backward compatible)
- `memory_human`: "1.08 GB" (NEW - easier to read)

## Common Workflows

### Free a Stuck Port
```bash
# 1. Find what's using the port
@secure-dev-manager netstat 8000

# 2. Kill the process tree
@secure-dev-manager killall [PID]
```

### Clean Development Environment
```bash
# 1. Check current status
@secure-dev-manager status

# 2. Find specific processes
@secure-dev-manager ps python
@secure-dev-manager ps node

# 3. Kill unwanted processes
@secure-dev-manager killall [PID]
```

### Start Development Server
```bash
# 1. Check port is free
@secure-dev-manager netstat 3000

# 2. Start server in background
@secure-dev-manager execute_command "npm run dev" --cwd "C:/projects/myapp" --background

# 3. Verify it's running
@secure-dev-manager status
```

### Safe Process Termination
```bash
# 1. Find the process
@secure-dev-manager ps server

# 2. Preview what would be killed
@secure-dev-manager kill [PID] --dry-run

# 3. Check for children
@secure-dev-manager ps [PID] --mode=full

# 4. Kill appropriately
@secure-dev-manager kill [PID]      # If no children
@secure-dev-manager killall [PID]   # If has children
```

## Tips & Tricks

### Speed Optimization
- Use `--mode=instant` for listing many processes
- Use `--mode=quick` when you don't need CPU%
- Default `smart` mode auto-optimizes based on process type

### Safety First
- Always use `--dry-run` when unsure
- Check for children before killing
- Use `killall` to prevent orphans

### Chrome Management
```bash
# Quick Chrome cleanup
@secure-dev-manager kill_all_chrome --confirm
```

## Error Messages Guide

| Error | Solution |
|-------|----------|
| "Process was spawned by this tool" | Add `--override` |
| "Process has child processes" | Use `killall` instead |
| "Cannot kill protected process" | This is MCP infrastructure - don't kill |
| "Port in use by multiple processes" | Use `killall` on parent |

## Version History

- **v3.2**: Command aliases, dry-run, human-readable memory
- **v3.1**: Override parameter, better errors
- **v3.0**: Performance modes, orphan prevention

---

**Remember**: When in doubt, use `--dry-run` first!
