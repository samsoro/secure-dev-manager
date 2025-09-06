# Release Checklist

## Before Release

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with version notes
- [ ] Version number updated in secure_dev_manager.py
- [ ] Examples tested and working

## Creating a Release

1. **Tag the release**
   ```bash
   git tag -a v3.2.0 -m "Version 3.2.0 - The Alias Update"
   git push origin v3.2.0
   ```

2. **Create GitHub Release**
   - Go to https://github.com/samsoro/secure-dev-manager/releases
   - Click "Create a new release"
   - Choose the tag you just created
   - Title: "v3.2.0 - The Alias Update"
   - Description: Copy from CHANGELOG.md

3. **Update MCP Registries**
   - Submit PR to https://github.com/modelcontextprotocol/servers
   - Update listing on https://mcpservers.org/
   - Add to https://mcpmarket.com/

## Release Notes Template

```markdown
## 🎉 Secure Dev Manager v3.2.0 - The Alias Update

### What's New
- 🆕 Unix-style command aliases (ps, kill, netstat)
- 🔍 Dry-run mode for safe operation preview
- 📊 Human-readable memory display

### Highlights
- Never reboot for stuck ports again
- Protects MCP infrastructure automatically
- 19x faster than traditional scripts

### Installation
```bash
pip install psutil
python install.py
```

### Quick Start
```bash
@secure-dev-manager status
@secure-dev-manager ps python
@secure-dev-manager netstat 8000
```

Full documentation: [README.md](README.md)
```
