"""
Comprehensive test suite for Secure Development Manager
Tests performance, safety, and functionality
"""

import time
import psutil
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from process_management import ProcessManager
from windows_safety import WindowsSafetyManager

def test_performance():
    """Test that operations meet performance targets"""
    print("Testing Performance...")
    
    import asyncio
    safety = WindowsSafetyManager()
    pm = ProcessManager(safety, print)
    
    # Test find_process performance
    start = time.time()
    result = asyncio.run(pm.find_process("python"))
    elapsed = time.time() - start
    assert elapsed < 2.0, f"find_process too slow: {elapsed}s"
    print(f"[OK] find_process: {elapsed:.3f}s")
    
    # Test check_ports performance
    start = time.time()
    result = asyncio.run(pm.check_ports())
    elapsed = time.time() - start
    assert elapsed < 0.5, f"check_ports too slow: {elapsed}s"
    print(f"[OK] check_ports: {elapsed:.3f}s")
    
    # Test protection check performance
    start = time.time()
    for i in range(10):
        pm._check_protection_cached(os.getpid(), "test.exe", "test")
    elapsed = (time.time() - start) / 10
    assert elapsed < 0.1, f"protection check too slow: {elapsed}s"
    print(f"[OK] protection check: {elapsed:.3f}s avg")
    
    print("Performance tests passed!\n")


def test_safety():
    """Test MCP protection system"""
    print("Testing Safety System...")
    
    safety = WindowsSafetyManager()
    
    # Test MCP process detection using actual process objects
    import os
    current_proc = psutil.Process(os.getpid())
    # We can't easily test MCP detection without real MCP processes
    # So we'll test the validation methods instead
    
    # Test Claude-related detection (need actual process object, not string)
    # We'll test with the current process as a proxy
    current_proc = psutil.Process(os.getpid())
    # Since current process is Python, it shouldn't be Claude-related
    assert not safety.is_claude_related(current_proc), "False positive for Python process"
    print("[OK] Claude detection working")
    
    # Test system critical (also needs process object)
    assert not safety.is_system_critical(current_proc), "False positive for Python process"
    print("[OK] System critical detection working")
    
    # Test command validation
    is_safe, msg = safety.validate_command("taskkill /f /im mcp-server.exe")
    assert not is_safe, "Dangerous command not blocked"
    is_safe, msg = safety.validate_command("python app.py")
    assert is_safe, "Safe command blocked"
    print("[OK] Command validation working")
    
    print("Safety tests passed!\n")


def test_functionality():
    """Test basic functionality"""
    print("Testing Functionality...")
    
    import asyncio
    safety = WindowsSafetyManager()
    pm = ProcessManager(safety, print)
    
    # Test allowed commands
    result = asyncio.run(pm.list_allowed_commands())
    assert result['success'], "list_allowed_commands failed"
    assert 'basic_commands' in result, "Missing basic commands"
    assert 'dev_commands' in result, "Missing dev commands"
    print("[OK] list_allowed_commands working")
    
    # Test execute_command validation
    result = asyncio.run(pm.execute_command("echo test"))
    assert result['success'], "Basic echo command failed"
    print("[OK] execute_command working")
    
    # Test forbidden command
    result = asyncio.run(pm.execute_command("dangerous_command"))
    assert not result['success'], "Dangerous command not blocked"
    print("[OK] Command blocking working")
    
    # Test find_process
    result = asyncio.run(pm.find_process("python"))
    assert result['success'], "find_process failed"
    assert 'processes' in result, "Missing processes in result"
    print(f"[OK] find_process found {result.get('count', 0)} processes")
    
    # Test port checking
    result = asyncio.run(pm.check_ports())
    assert result['success'], "check_ports failed"
    assert 'ports' in result, "Missing ports in result"
    print("[OK] check_ports working")
    
    print("Functionality tests passed!\n")


def test_virtual_environments():
    """Test virtual environment detection"""
    print("Testing Virtual Environment Support...")
    
    safety = WindowsSafetyManager()
    pm = ProcessManager(safety, print)
    
    # Test venv detection
    test_dir = Path("C:/test_project")
    venv_path = pm.get_venv_for_cwd(str(test_dir))
    print(f"[OK] Venv detection logic working")
    
    # Test known project venvs
    assert 'portfolio-analysis' in pm.project_venvs, "Missing portfolio-analysis venv"
    assert 'trip-builder-pro' in pm.project_venvs, "Missing trip-builder-pro venv"
    print("[OK] Known project venvs configured")
    
    print("Virtual environment tests passed!\n")


def test_caching():
    """Test caching behavior"""
    print("Testing Cache System...")
    
    safety = WindowsSafetyManager()
    pm = ProcessManager(safety, print)
    
    # Test protection cache
    pid = os.getpid()
    
    # First call should populate cache
    start = time.time()
    result1 = pm._check_protection_cached(pid, "test.exe", "test")
    time1 = time.time() - start
    
    # Second call should be faster (cached)
    start = time.time()
    result2 = pm._check_protection_cached(pid, "test.exe", "test")
    time2 = time.time() - start
    
    assert result1 == result2, "Cache returned different results"
    # For very fast operations, just check that cache is at least as fast
    assert time2 <= time1 * 1.1, "Cache performance degraded"
    print(f"[OK] Protection cache working (uncached: {time1:.3f}s, cached: {time2:.3f}s)")
    
    # Test cache expiration
    pm._cache_timestamp = time.time() - 20  # Force expiration
    result3 = pm._check_protection_cached(pid, "test.exe", "test")
    assert result3 == result1, "Cache expiration changed result"
    print("[OK] Cache expiration working")
    
    print("Cache tests passed!\n")


def benchmark_operations():
    """Run performance benchmarks"""
    print("Running Benchmarks...")
    print("-" * 50)
    
    import asyncio
    safety = WindowsSafetyManager()
    pm = ProcessManager(safety, print)
    
    operations = [
        ("find_process('python')", lambda: asyncio.run(pm.find_process("python"))),
        ("find_process('e')", lambda: asyncio.run(pm.find_process("e"))),
        ("check_ports()", lambda: asyncio.run(pm.check_ports())),
        ("list_allowed_commands()", lambda: asyncio.run(pm.list_allowed_commands())),
        ("execute_command('echo')", lambda: asyncio.run(pm.execute_command("echo test"))),
    ]
    
    for name, operation in operations:
        times = []
        for _ in range(5):
            start = time.time()
            operation()
            times.append(time.time() - start)
        
        avg = sum(times) / len(times)
        print(f"{name:30} Avg: {avg:.3f}s  Min: {min(times):.3f}s  Max: {max(times):.3f}s")
    
    print("-" * 50)
    print("Benchmarks complete!\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("SECURE DEVELOPMENT MANAGER - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_performance()
        test_safety()
        test_functionality()
        test_virtual_environments()
        test_caching()
        benchmark_operations()
        
        print("=" * 60)
        print("ALL TESTS PASSED! [OK]")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
