# Changelog

## Version 3.2 - The Alias Update (2025-09-06)

### Added
- **Command Aliases** - Use familiar Unix-style commands:
  - `ps` → `find_process`
  - `kill` → `kill_process`
  - `killall` → `kill_process_tree`
  - `netstat` → `check_ports`
  - `status` → `dev_status`
- **Dry Run Support** - Preview what would be killed with `--dry-run` parameter
- **Human-Readable Memory** - New `memory_human` field shows "2.4 GB" format alongside `memory_mb`

### Developer Experience
- Based on feedback from senior Windows developer testing
- Reduces friction for Unix-familiar developers
- Maintains full backward compatibility
- Zero breaking changes

### Implementation Notes
- Aliases handled at MCP layer for seamless integration
- Dry run works for all kill operations
- Memory formatting automatically adjusts units (MB vs GB)

---

## Version 3.1 - Developer Experience Edition

### Added
- **Override Parameter**: Now properly exposed for bypassing user-spawned protection
  - Use `override=true` to force kill processes you started
- **Better Error Messages**: Every error now includes examples and suggestions
  - No more confusion about "--override" vs "override=true"
  - Developer hints explain why protection exists

### Fixed
- Override parameter properly exposed in API
- Clear error messages guide users to the right solution

---

## Version 3.0 - Performance Revolution

### Major Features
- **Smart Defaults**: Automatically detects process type and optimizes
- **Multiple Performance Modes**:
  - `instant`: <0.05s - Just PIDs and names
  - `quick`: <0.2s - Basic info, no children
  - `smart`: Auto-optimized based on process type
  - `full`: Everything including children
- **Accurate PID Reporting**: Returns actual process PID, not cmd.exe wrapper
- **Port Wait Logic**: Optionally wait for ports to become active after starting servers

### Performance Improvements
- 90x faster process enumeration (45s → 0.5s)
- Parallel port checking
- Smart caching system
- Optimized child process detection
