# Contributing to Secure Dev Manager

First off, thank you for considering contributing to Secure Dev Manager! 🎉

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, please include:

- Your operating system (Windows version)
- Python version
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Any error messages

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- Use case for the feature
- Proposed implementation approach (if you have one)
- Any potential drawbacks or considerations

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests that cover it
3. Ensure the test suite passes
4. Update documentation as needed
5. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/secure-dev-manager.git
cd secure-dev-manager

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Test with Claude Desktop
python secure_dev_manager.py
```

## Code Style

- Follow PEP 8
- Use descriptive variable names
- Add comments for complex logic
- Keep functions focused and small
- Document all public functions

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for good test coverage
- Test on Windows (primary platform)

## Safety First

Remember, this tool's primary purpose is safety:

1. **Never compromise MCP protection** - The tool must never allow killing MCP processes
2. **Prevent orphans** - Always handle process trees properly
3. **Clear errors** - Error messages should guide users to solutions
4. **Performance matters** - Keep operations fast (<1 second)

## Questions?

Feel free to open an issue for any questions about contributing!
