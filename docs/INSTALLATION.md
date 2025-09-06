# Installation & Requirements

## System Requirements

### Operating System
- **Windows 10 or Windows 11** (required)
- Administrator privileges (recommended for some operations)

### Python
- **Python 3.8 or higher** (required)
- Available in PATH or specify full path in Claude Desktop config

### Claude Desktop
- Latest version of Claude Desktop
- MCP (Model Context Protocol) support enabled

## Dependencies

### Required Dependencies

#### psutil
Process and system utilities library.

```bash
pip install psutil
```

**Purpose**: 
- Process enumeration and information
- CPU and memory monitoring
- Network connection detection
- Process relationship tracking

**Version**: Latest stable (6.0.0+)

### Optional Dependencies

#### pywin32 (Recommended)
Python extensions for Windows.

```bash
pip install pywin32
```

**Purpose**:
- Windows Job Objects for atomic process tree termination
- Enhanced orphan prevention
- Cleaner background process management

**Benefits when installed**:
- Background processes started with `execute_command --background` use Job Objects
- Entire process trees terminate atomically
- No possibility of orphaned processes when using Job Objects

**Works without it**:
- System still prevents orphans through manual tree termination
- Warns before creating orphans
- `kill_process_tree` still works using bottom-up termination

## Installation Steps

### 1. Basic Installation

```bash
# Install Python (if not already installed)
# Download from python.org or use Windows Store

# Install required dependency
pip install psutil

# Optional but recommended for best orphan prevention
pip install pywin32
```

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:
`%APPDATA%\Claude\claude_desktop_config.json`

Add the secure-dev-manager configuration:

```json
{
  "mcpServers": {
    "secure-dev": {
      "command": "python",
      "args": ["C:\\Users\\Bizon\\AI-Projects\\mcp-infrastructure\\servers\\secure-dev\\secure_dev_manager.py"]
    }
  }
}
```

**Note**: Adjust the path to match your installation location.

### 3. Verify Installation

1. Restart Claude Desktop
2. Check if the tool appears in your toolbox
3. Test with: `@secure-dev-manager list_allowed`

## Troubleshooting Installation

### Issue: "psutil not found"

```bash
# Ensure psutil is installed for the correct Python version
python -m pip install psutil

# Or if using Python 3 explicitly
python3 -m pip install psutil
```

### Issue: "pywin32 import failed"

This is non-critical. The system works without pywin32 but with reduced functionality:
- Manual tree termination still works
- Orphan warnings still work
- Only Job Objects are unavailable

To fix:
```bash
# Install pywin32
pip install pywin32

# If issues persist, try:
python -m pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

### Issue: "MCP server not found in Claude Desktop"

1. Check the configuration path is correct
2. Ensure Python is in PATH or use full path:
```json
{
  "command": "C:\\Python312\\python.exe",
  "args": ["C:\\full\\path\\to\\secure_dev_manager.py"]
}
```
3. Check debug log: `secure-dev-manager_debug.log`

### Issue: "Permission denied" errors

Some operations may require administrator privileges:
1. Run Claude Desktop as Administrator (not recommended for daily use)
2. Or accept that some system processes cannot be managed

## Platform Support

### Windows
✅ **Fully Supported**
- All features available
- Job Objects with pywin32
- Process tree management
- Port detection

### macOS
❌ **Not Supported**
- Windows-specific implementation
- Would require significant modifications
- Consider alternative MCP servers for macOS

### Linux
❌ **Not Supported**
- Windows-specific implementation
- Different process management model
- Consider alternative MCP servers for Linux

## Performance Considerations

### With pywin32 Installed
- Job Object creation: ~5ms overhead
- Atomic tree termination: Instant
- Memory overhead: Minimal (~1MB)

### Without pywin32
- Manual tree termination: ~10-50ms depending on tree size
- Still effective, just not atomic
- No additional memory overhead

## Security Notes

1. **MCP Protection**: Always active, regardless of dependencies
2. **Command Whitelisting**: Not affected by optional dependencies
3. **Process Validation**: Full validation regardless of pywin32

## Version Compatibility

| Component | Minimum Version | Recommended Version | Notes |
|-----------|----------------|-------------------|--------|
| Python | 3.8 | 3.12+ | Better performance in newer versions |
| psutil | 5.9.0 | 6.0.0+ | Latest has better Windows support |
| pywin32 | 305 | 311+ | Recent versions have bug fixes |
| Windows | Windows 10 1809 | Windows 11 | Better process management in Win11 |

## Update Instructions

To update the secure-dev-manager:

1. **Update dependencies**:
```bash
pip install --upgrade psutil
pip install --upgrade pywin32  # if installed
```

2. **Update the server files**:
- Pull latest from repository
- Or manually update the Python files

3. **Restart Claude Desktop** to load the updated server

## Uninstallation

To remove the secure-dev-manager:

1. **Remove from Claude Desktop config**:
   - Edit `%APPDATA%\Claude\claude_desktop_config.json`
   - Remove the "secure-dev" section

2. **Optional: Uninstall Python packages**:
```bash
pip uninstall psutil
pip uninstall pywin32  # if installed
```

3. **Delete server files** (optional)

## Support

For issues or questions:
1. Check the debug log: `secure-dev-manager_debug.log`
2. Review the [Troubleshooting Guide](DEVELOPER_GUIDE.md#troubleshooting-guide)
3. Ensure all dependencies are correctly installed
4. Verify Windows version compatibility
