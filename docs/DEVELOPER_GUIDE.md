# Developer Guide

Practical guide for developers using the Secure Development Manager in their daily workflow.

## Table of Contents

1. [Common Workflows](#common-workflows)
2. [Development Patterns](#development-patterns)
3. [Troubleshooting Guide](#troubleshooting-guide)
4. [Best Practices](#best-practices)
5. [Advanced Usage](#advanced-usage)
6. [Real-World Examples](#real-world-examples)

---

## Common Workflows

### Starting a Development Server

**Scenario**: You need to start a React development server and keep it running.

```bash
# 1. Check if port is free (using netstat alias)
@secure-dev-manager netstat 3000

# 2. Navigate and start server in background
@secure-dev-manager execute_command "npm run dev" --cwd "C:/projects/my-react-app" --background

# 3. Verify it's running (using status alias)
@secure-dev-manager status
```

### Cleaning Up Stuck Processes

**Scenario**: Port 8000 is blocked by an old Django server.

```bash
# 1. Find what's using the port (using netstat alias)
@secure-dev-manager netstat 8000
# Output: Port 8000 in use by python.exe (PID: 12345)
#         Has 3 child processes

# 2. Preview what would be killed (NEW in v3.2)
@secure-dev-manager killall 12345 --dry-run
# Shows: Would kill 4 processes

# 3. Terminate the entire process tree (no orphans!)
@secure-dev-manager killall 12345
# All 4 processes terminated

# 4. Verify port is free
@secure-dev-manager netstat 8000
```

### Managing Python Virtual Environments

**Scenario**: Running Python scripts with correct virtual environment.

```python
# Automatic venv detection
@secure-dev-manager execute_command "python manage.py migrate" --cwd "C:/projects/django-app"
# Automatically uses C:/projects/django-app/.venv

# Install packages in venv
@secure-dev-manager execute_command "pip install django" --cwd "C:/projects/django-app"

# Check installed packages
@secure-dev-manager execute_command "pip list" --cwd "C:/projects/django-app"
```

### Finding and Managing Node Processes

**Scenario**: Multiple Node.js servers running, need to find specific one.

```bash
# 1. Find all Node processes (using ps alias)
@secure-dev-manager ps node

# 2. Use instant mode for faster results
@secure-dev-manager ps node --mode=instant

# 3. Find specific Node app by arguments
@secure-dev-manager ps "server.js" --include-args

# 4. Kill specific process (using kill alias)
@secure-dev-manager kill 23456
```

### Handling User-Spawned Processes (v3.1)

**Scenario**: You started a process with secure-dev-manager and need to kill it.

```python
# Start a background process
@secure-dev-manager execute_command "python dev_server.py" --background
# Returns: Started with PID 12345

# Later, try to kill it (protected by default)
@secure-dev-manager kill_process 12345
# Error: Process was spawned by this tool
# Suggestion: Use override=true to force termination

# Option 1: Use override to bypass protection
@secure-dev-manager kill_process 12345 --override
# Success: Process terminated

# Option 2: Use kill_process_tree for clean cleanup
@secure-dev-manager kill_process_tree 12345
# Success: Process tree terminated (includes any children)
```

**Why User-Spawned Protection Exists**:
- Prevents accidental termination of processes you started
- Encourages use of `kill_process_tree` to avoid orphans
- Provides safety net for background development servers
- Can be bypassed with `--override` when you're certain

---

## Development Patterns

### Pattern 1: Safe Server Restart

```python
# Function to safely restart a development server
def restart_dev_server(port, start_command, project_dir):
    # 1. Check current status
    port_status = check_ports(port)
    
    if port_status['status'] == 'in_use':
        # 2. Kill existing process
        pid = port_status['process']['pid']
        kill_process(pid)
        
        # 3. Wait for port to be free
        time.sleep(1)
    
    # 4. Start new server
    execute_command(start_command, cwd=project_dir, background=True)
    
    # 5. Verify it started
    time.sleep(2)
    return check_ports(port)

# Usage
restart_dev_server(3000, "npm run dev", "C:/projects/frontend")
```

### Pattern 2: Multi-Project Management

```python
# Managing multiple projects simultaneously
projects = {
    "frontend": {
        "path": "C:/projects/frontend",
        "command": "npm run dev",
        "port": 3000
    },
    "backend": {
        "path": "C:/projects/backend",
        "command": "python app.py",
        "port": 5000
    },
    "admin": {
        "path": "C:/projects/admin",
        "command": "npm start",
        "port": 3001
    }
}

# Start all projects
for name, config in projects.items():
    print(f"Starting {name}...")
    execute_command(config['command'], cwd=config['path'], background=True)

# Check all statuses
server_status()
```

### Pattern 3: Dependency Installation

```python
# Install dependencies for multiple package managers
def install_dependencies(project_path):
    # Check for package.json
    if exists(f"{project_path}/package.json"):
        execute_command("npm install", cwd=project_path)
    
    # Check for requirements.txt
    if exists(f"{project_path}/requirements.txt"):
        execute_command("pip install -r requirements.txt", cwd=project_path)
    
    # Check for Gemfile
    if exists(f"{project_path}/Gemfile"):
        execute_command("bundle install", cwd=project_path)
```

### Pattern 4: Process Monitoring

```python
# Monitor resource usage of development processes
def monitor_dev_processes():
    processes = find_process("python")
    processes += find_process("node")
    
    # Sort by CPU usage
    sorted_procs = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)
    
    # Alert on high usage
    for proc in sorted_procs:
        if proc['cpu_percent'] > 80:
            print(f"High CPU: {proc['name']} ({proc['pid']}) - {proc['cpu_percent']}%")
        if proc['memory_mb'] > 1000:
            print(f"High Memory: {proc['name']} ({proc['pid']}) - {proc['memory_mb']}MB")
```

---

## Troubleshooting Guide

### Issue: "Command not allowed"

**Symptom**: 
```
Error: Command 'docker ps' is not in the allowed commands list
```

**Solution**:
1. Check allowed commands: `@secure-dev-manager list_allowed`
2. Use an alternative allowed command
3. Or add to allowed commands in `process_management.py`:
```python
self.dev_commands.add('docker ps')
```

### Issue: "Cannot kill protected MCP process"

**Symptom**:
```
Error: Cannot kill protected MCP process
Process 'mcp-server.exe' (PID: 12345) is part of MCP infrastructure
```

**Solution**:
1. This is by design - MCP processes are protected
2. Check if you're targeting the right process
3. Use `find_process` to find non-protected alternatives
4. If absolutely necessary, use Task Manager (not recommended)

### Issue: Virtual environment not detected

**Symptom**:
```
Using system Python instead of project venv
```

**Solution**:
1. Ensure `.venv` exists in project directory
2. Check venv is properly created:
```python
@secure-dev-manager execute_command "python -m venv .venv" --cwd "C:/projects/myapp"
```
3. Verify with: `@secure-dev-manager execute_command "pip list" --cwd "C:/projects/myapp"`

### Issue: Port shows as in use but no process found

**Symptom**:
```
Port 3000 in use but process not found
```

**Solution**:
1. Check for orphaned child processes:
```python
@secure-dev-manager check_ports 3000
# Look for "multiple processes" in output
```
2. If orphaned processes exist, use tree kill:
```python
@secure-dev-manager kill_process_tree [parent_pid]
```
3. The process might have elevated privileges
4. Try running Claude Desktop as administrator
5. With orphan prevention, reboots should rarely be needed!

### Issue: Process has child processes warning

**Symptom**:
```
Error: Process has child processes
Warning: Killing this process would orphan 3 child process(es)
```

**Solution**:
1. This is the orphan prevention system working!
2. Use `kill_process_tree` instead:
```python
@secure-dev-manager kill_process_tree [pid]
```
3. All children will be terminated with the parent
4. No orphaned processes left behind

### Issue: Background process dies immediately

**Symptom**:
```
Started process with --background but it exits immediately
```

**Solution**:
1. Check the command works in foreground first
2. Ensure working directory is correct
3. Check for missing dependencies
4. Review output in debug log
5. Some commands need specific environment variables

---

## Best Practices

### 1. Process Management

**DO**:
- Always check protection status before killing
- Use `find_process` to verify PID before operations
- Clean up background processes when done
- Monitor resource usage regularly

**DON'T**:
- Force kill unless necessary
- Assume process names are unique
- Kill system or MCP processes
- Leave orphaned servers running

### 2. Port Management

**DO**:
- Check ports before starting servers
- Use standard development ports
- Clean up ports after development
- Document which service uses which port

**DON'T**:
- Hard-code port numbers
- Use system ports (<1024) without admin rights
- Leave services on production ports

### 3. Virtual Environment Management

**DO**:
- Keep venv in project root as `.venv`
- Use `--cwd` to ensure correct venv activation
- Install dependencies in venv, not globally
- Document Python version requirements

**DON'T**:
- Mix global and venv packages
- Share venvs between projects
- Forget to activate venv for scripts

### 4. Command Execution

**DO**:
- Use `--background` for long-running processes
- Specify working directory explicitly
- Check command is whitelisted first
- Capture output for debugging

**DON'T**:
- Execute untrusted commands
- Use shell injection patterns
- Ignore error messages
- Run multiple instances of same server

---

## Advanced Usage

### Custom Tool Integration

**Adding Docker support**:

```python
# In process_management.py
class ProcessManager:
    def __init__(self, safety_manager, debug_log):
        # ... existing code ...
        
        # Add Docker commands
        self.docker_commands = {
            'docker ps', 'docker images', 'docker logs',
            'docker-compose up', 'docker-compose down',
            'docker-compose ps', 'docker-compose logs'
        }
        self.allowed_commands.update(self.docker_commands)
        
    def manage_containers(self, action, container=None):
        """Manage Docker containers"""
        if action == 'list':
            return self.execute_command("docker ps -a")
        elif action == 'stop' and container:
            return self.execute_command(f"docker stop {container}")
        elif action == 'remove' and container:
            return self.execute_command(f"docker rm {container}")
```

### Performance Monitoring

**Creating a performance dashboard**:

```python
def performance_dashboard():
    """Get comprehensive system performance metrics"""
    
    # Get all dev processes
    python_procs = find_process("python")
    node_procs = find_process("node")
    
    # Check all ports
    port_status = check_ports()
    
    # Get managed servers
    servers = server_status()
    
    # Compile metrics
    metrics = {
        "processes": {
            "python": len(python_procs),
            "node": len(node_procs),
            "total_cpu": sum(p['cpu_percent'] for p in python_procs + node_procs),
            "total_memory_mb": sum(p['memory_mb'] for p in python_procs + node_procs)
        },
        "ports": {
            "in_use": len([p for p in port_status if p['status'] == 'in_use']),
            "free": len([p for p in port_status if p['status'] == 'free'])
        },
        "servers": {
            "managed": len(servers['managed_servers']),
            "running": len([s for s in servers['managed_servers'].values() if s['status'] == 'running'])
        }
    }
    
    return metrics
```

### Batch Operations

**Batch process cleanup**:

```python
def cleanup_dev_processes(exclude_ports=[]):
    """Clean up all development processes except those on excluded ports"""
    
    # Find all dev processes
    processes = find_process("python") + find_process("node")
    
    # Filter out protected and excluded
    to_kill = []
    for proc in processes:
        # Skip protected
        if proc['protected']:
            continue
            
        # Skip if on excluded port
        port_check = check_ports()
        proc_port = None
        for port_info in port_check:
            if port_info.get('process', {}).get('pid') == proc['pid']:
                proc_port = port_info['port']
                break
        
        if proc_port not in exclude_ports:
            to_kill.append(proc['pid'])
    
    # Kill all selected processes
    results = []
    for pid in to_kill:
        results.append(kill_process(pid))
    
    return results

# Keep port 3000 and 8000 services running, kill everything else
cleanup_dev_processes(exclude_ports=[3000, 8000])
```

---

## Real-World Examples

### Example 1: Full Stack Development Setup

```python
# Complete setup for full-stack development

# 1. Check system status
@secure-dev-manager server_status

# 2. Clean up any stuck processes
@secure-dev-manager find_process python
@secure-dev-manager find_process node

# 3. Start backend API
@secure-dev-manager execute_command "python manage.py runserver" --cwd "C:/projects/backend" --background

# 4. Start frontend
@secure-dev-manager execute_command "npm run dev" --cwd "C:/projects/frontend" --background

# 5. Start Redis for caching
@secure-dev-manager execute_command "redis-server" --background

# 6. Verify everything is running
@secure-dev-manager check_ports
@secure-dev-manager server_status
```

### Example 2: Debugging High CPU Usage

```python
# Find and diagnose high CPU usage

# 1. Find all Python processes
@secure-dev-manager find_process python

# Look for high cpu_percent values
# Example output: python.exe (PID: 12345) - CPU: 95%, Memory: 250MB

# 2. Get more details about the problematic process
@secure-dev-manager find_process 12345 --show-full-cmdline

# 3. If it's not critical, terminate it
@secure-dev-manager kill_process 12345

# 4. If it doesn't respond, force kill
@secure-dev-manager kill_process 12345 --force
```

### Example 3: Automated Testing Environment

```python
# Set up automated testing environment

# 1. Start test database
@secure-dev-manager execute_command "docker-compose up -d db" --cwd "C:/projects/test-env"

# 2. Run migrations
@secure-dev-manager execute_command "python manage.py migrate" --cwd "C:/projects/backend"

# 3. Load test data
@secure-dev-manager execute_command "python manage.py loaddata fixtures/test_data.json" --cwd "C:/projects/backend"

# 4. Start test server
@secure-dev-manager execute_command "python manage.py runserver --settings=settings.test" --cwd "C:/projects/backend" --background

# 5. Run tests
@secure-dev-manager execute_command "pytest tests/ -v" --cwd "C:/projects/backend"

# 6. Clean up
@secure-dev-manager find_process "manage.py"
# Kill test server process
```

### Example 4: Multi-Environment Development

```python
# Managing development, staging, and test environments

# Development on port 8000
@secure-dev-manager execute_command "python manage.py runserver 8000" --cwd "C:/projects/dev" --background

# Staging on port 8001
@secure-dev-manager execute_command "python manage.py runserver 8001 --settings=settings.staging" --cwd "C:/projects/staging" --background

# Test on port 8002
@secure-dev-manager execute_command "python manage.py runserver 8002 --settings=settings.test" --cwd "C:/projects/test" --background

# Monitor all environments
@secure-dev-manager server_status
@secure-dev-manager check_ports 8000
@secure-dev-manager check_ports 8001
@secure-dev-manager check_ports 8002
```

---

## Tips and Tricks

### Quick Commands

```python
# Kill all Python dev servers (not MCP)
@secure-dev-manager find_process "manage.py" --include-args
# Then kill non-protected ones

# Free up all development ports
for port in [3000, 5000, 8000, 8080, 5173, 4200]:
    @secure-dev-manager check_ports {port}
    # Kill if needed

# Check what's eating memory
@secure-dev-manager find_process python
# Look for memory_mb values

# Quick Django management
@secure-dev-manager execute_command "python manage.py shell" --cwd "C:/projects/django"
@secure-dev-manager execute_command "python manage.py makemigrations" --cwd "C:/projects/django"
@secure-dev-manager execute_command "python manage.py createsuperuser" --cwd "C:/projects/django"
```

### Productivity Aliases

Create these as saved commands:

```python
# dev-start: Start all development servers
# dev-stop: Stop all development servers  
# dev-status: Check all development services
# dev-clean: Clean up stuck processes
# dev-ports: Check all development ports
# dev-install: Install all dependencies
```

---

## Conclusion

The Secure Development Manager streamlines development workflows while maintaining safety and performance. By following these patterns and best practices, you can efficiently manage your development environment without risking MCP infrastructure.

Remember:
- Safety first - MCP processes are protected
- Use background mode for servers
- Clean up resources when done
- Monitor performance regularly
- Check the debug log when issues occur

Happy developing! 🚀