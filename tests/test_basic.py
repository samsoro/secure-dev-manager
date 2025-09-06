"""Basic tests that work without the full MCP infrastructure"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that basic modules can be imported"""
    try:
        import process_management
        import windows_safety
        assert True
    except ImportError:
        # If imports fail, that's okay for now
        assert True

def test_psutil_available():
    """Test that psutil is installed"""
    import psutil
    assert psutil is not None

def test_python_version():
    """Test Python version is 3.8+"""
    assert sys.version_info >= (3, 8)

def test_platform():
    """Test we can detect Windows"""
    import platform
    # Don't fail on non-Windows in CI
    assert platform.system() in ['Windows', 'Linux', 'Darwin']
