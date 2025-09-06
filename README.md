# Secure Development Manager MCP Server

[![Performance](https://img.shields.io/badge/Performance-10--19x%20Faster-brightgreen)](docs/PERFORMANCE.md)
[![Safety](https://img.shields.io/badge/MCP%20Safety-100%25-blue)](docs/ARCHITECTURE.md#safety-system)
[![Orphan Prevention](https://img.shields.io/badge/Orphan%20Prevention-100%25-green)](docs/WHY_USE_THIS.md)
[![Windows](https://img.shields.io/badge/Platform-Windows-informational)](docs/TECHNICAL.md)

A high-performance MCP server that solves Windows process management pain points: **prevents orphaned processes**, **protects MCP infrastructure**, and **provides transparency** into process relationships.

## 🎯 Version 3.2 - The Alias Update

**NEW**: Command aliases for Unix-style commands + dry-run support + human-readable memory!

### What's New in V3.2 (Latest)
- **Command Aliases**: Use familiar Unix-style commands
  - `ps` → `find_process`
  - `kill` → `kill_process`
  - `killall` → `kill_process_tree`
  - `netstat` → `check_ports`
  - `status` → `dev_status`
- **Dry Run Support**: Preview what would be killed with `--dry-run`
- **Human-Readable Memory**: Shows "2.4 GB" instead of just MB values

### What's New in V3.1
- **Override Parameter**: Now properly exposed for bypassing user-spawned protection
  - Use `override=true` to force kill processes you started
  - Clear error messages guide you to the right solution
- **Better Error Messages**: Every error now includes examples and suggestions
  - No more confusion about "--override" vs "override=true"
  - Developer hints explain why protection exists

### V3.0 Features (Still Amazing!)
- **Smart Defaults**: Automatically detects process type and optimizes
  - Browsers (Chrome, Firefox): Skip children checks, use quick mode
  - Dev tools (Python, Node): Include children and full info
- **Multiple Performance Modes**:
  - `instant`: <0.05s - Just PIDs and names
  - `quick`: <0.2s - Basic info, no children
  - `smart`: Auto-optimized based on process type
  - `full`: Everything including children
- **Accurate PID Reporting**: Returns actual process PID, not cmd.exe wrapper
- **Port Wait Logic**: Optionally wait for ports to become active after starting servers

## 🎯 Why Use This Instead of Scripts?

**The Problem**: Your custom scripts can accidentally kill MCP servers or leave orphaned processes that keep ports bound (requiring reboots).

**The Solution**: This tool handles all the complexity for you:
- ✅ **Prevents orphaned processes** - No more stuck ports!
- ✅ **Protects MCP servers** - Can't accidentally break Claude Desktop
- ✅ **Shows process relationships** - See parent-child hierarchies
- ✅ **19x faster** than typical process enumeration scripts

👉 **[Read the full comparison: Why Use This Tool?](docs/WHY_USE_THIS.md)**

## 💻 System Requirements

- **OS**: Windows 10/11
- **Python**: 3.8 or higher
- **Required**: `psutil` package
- **Optional**: `pywin32` package (for enhanced orphan prevention with Job Objects)

👉 See [Installation Guide](docs/INSTALLATION.md) for detailed requirements and setup instructions.

## 🔥 Features at a Glance

### Orphan Prevention (NEW!)
```python
# Problem: Killing parent leaves children holding ports
@secure-dev-manager kill_process 1234
> Error: Process has 3 child processes
> Use 'kill_process_tree' to prevent orphans

# Solution: Kill entire process family
@secure-dev-manager kill_process_tree 1234
> All 4 processes terminated
> Port freed immediately!
```

### MCP Protection
```python
# Can't accidentally kill Claude Desktop infrastructure
@secure-dev-manager find_process python
> PID 7600: secure_dev_manager.py [PROTECTED - MCP Infrastructure]
> PID 8900: my_script.py [Safe to kill]
```

### Process Transparency
```python
# See everything about your processes
@secure-dev-manager find_process node
> PID 1234: node.exe
>   Memory: 145MB, CPU: 2.5%
>   Children: 3 processes
>   Status: Can be killed safely
```

## ✨ All Features

- **🎯 Orphan Prevention**: Process tree management prevents stuck ports
  - Warns when killing would create orphans
  - `kill_process_tree` terminates entire families
  - Shows child count in process listings
  - No more "port in use" after killing servers!
  
- **🛡️ MCP Protection**: Can't accidentally break Claude Desktop
  - Automatic detection of MCP processes
  - Clear "PROTECTED" warnings
  - Safe command whitelisting
  
- **⚡ Blazing Performance**: 90x faster than typical scripts
  - Find processes in 0.5s (was 45s)
  - Parallel port checking
  - Smart caching system
  
- **💻 Developer Experience**: Built for real workflows
  - Virtual environment auto-detection
  - Background process management
  - Rich process information (CPU, memory, threads)
  - Clear error messages with solutions

## 🚀 Quick Start

### Installation

1. **Install required dependencies**:
```bash
pip install psutil
```

2. **Install optional dependencies** (for enhanced orphan prevention):
```bash
pip install pywin32  # Windows only - enables Job Objects for atomic process tree termination
```

3. **Configure Claude Desktop**:
Add to your Claude Desktop configuration (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "secure-dev": {
    "command": "python",
    "args": ["C:\\Users\\Bizon\\AI-Projects\\mcp-infrastructure\\servers\\secure-dev\\secure_dev_manager.py"]
  }
}
```

4. **Restart Claude Desktop** to load the tool

### Basic Usage

```bash
# Find processes (using Unix-style alias)
@secure-dev-manager ps python          # Find Python processes
@secure-dev-manager ps chrome          # Find Chrome processes
@secure-dev-manager ps node --mode=instant  # Ultra-fast search

# Check ports (using netstat alias)
@secure-dev-manager netstat            # Check all dev ports
@secure-dev-manager netstat 8000       # Check specific port

# Quick status overview
@secure-dev-manager status             # Dev environment overview

# Kill processes safely
@secure-dev-manager kill 12345 --dry-run    # Preview what would happen
@secure-dev-manager kill 12345              # Kill single process
@secure-dev-manager killall 12345           # Kill process + all children

# Execute commands
@secure-dev-manager execute_command "python app.py" --background

# Get detailed server status
@secure-dev-manager server_status
```

### User-Spawned Process Protection

```python
# Start a background process
@secure-dev-manager execute_command "python server.py" --background
> Started with PID 12345

# Try to kill it (protected by default)
@secure-dev-manager kill_process 12345
> Error: Process was spawned by this tool
> Use override=true to force termination

# Override the protection when needed
@secure-dev-manager kill_process 12345 --override
> Process terminated successfully

# Or use kill_process_tree for clean cleanup
@secure-dev-manager kill_process_tree 12345
> Process tree terminated successfully
```

## 📚 Documentation

### 🚀 Quick Start
- [**⚡ Quick Reference**](QUICK_REFERENCE.md) - Cheat sheet for daily use
- [**📝 Changelog**](CHANGELOG.md) - What's new in v3.1
- [**🎯 Why Use This Tool?**](docs/WHY_USE_THIS.md) - Comparison with custom scripts

### Essential Reading
- [**📦 Feature Summary**](docs/FEATURE_SUMMARY.md) - Quick overview card
- [**📑 Installation Guide**](docs/INSTALLATION.md) - System requirements and setup
- [**🆕 Upgrade Report**](UPGRADE_REPORT.md) - v3.1 improvements explained

### Developer Resources
- [**API Reference**](docs/API_REFERENCE.md) - Detailed tool documentation (updated for v3.1)
- [**Developer Guide**](docs/DEVELOPER_GUIDE.md) - Practical examples and patterns
- [**Examples**](examples/) - Code examples and use cases

### Technical Deep Dives
- [**Architecture Guide**](docs/ARCHITECTURE.md) - System design and internals
- [**Performance Guide**](docs/PERFORMANCE.md) - Optimization details
- [**Known Issues**](docs/KNOWN_ISSUES.md) - Current status & future improvements

## 🧪 Testing

Run the test suite:

```bash
# Run comprehensive tests
python tests/test_comprehensive.py

# Performance benchmarks
python tests/test_performance.py

# Safety validation
python tests/test_windows_safety.py
```

## 📈 Performance

From 45 seconds to 0.5 seconds through intelligent optimization:

| Operation | Before | After (V3) | Improvement |
|-----------|--------|------------|-------------|
| find_process("chrome") - 53 processes | 1.6s | 0.1s | 16x |
| find_process("python") - 5 processes | 0.2s | 0.2s | Maintained |
| check_ports() - 6 ports | 0.6s | 0.2s | 3x |
| instant mode - any process | N/A | 0.05s | New! |

## 🌳 Orphan Prevention Methods

The system uses two methods to prevent orphaned processes:

### Method 1: Manual Tree Termination (Default)
- Works without additional dependencies
- Kills child processes first (bottom-up)
- Then kills the parent process
- Effective but not atomic

### Method 2: Windows Job Objects (With pywin32)
- Requires `pip install pywin32`
- Creates Job Object for background processes
- Entire process tree dies atomically when Job is terminated
- Cleanest solution for preventing orphans

**Note**: Even without pywin32, the system effectively prevents orphans through manual tree termination and warnings.

## 🤝 Contributing

1. Keep safety as the top priority
2. Maintain sub-second performance
3. Add tests for new features
4. Update documentation
5. Follow existing code style

## 📄 License

Part of the symbiotic-mind-2 project ecosystem.

---

**Note**: This tool prioritizes safety over functionality. MCP processes are protected by design and cannot be terminated, ensuring Claude Desktop stability.