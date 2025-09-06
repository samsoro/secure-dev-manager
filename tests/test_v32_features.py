#!/usr/bin/env python3
"""
Test script for v3.2 features
Run this after restarting Claude Desktop to verify the improvements
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from windows_safety import WindowsSafetyManager
from process_management import ProcessManager

async def test_v32_features():
    """Test the new v3.2 features"""
    print("=== Testing v3.2 Features ===\n")
    
    # Initialize
    safety = WindowsSafetyManager()
    debug_log = lambda msg: print(f"[DEBUG] {msg}")
    pm = ProcessManager(safety, debug_log)
    
    # Test 1: Human-readable memory in find_process
    print("1. Testing human-readable memory format...")
    result = await pm.find_process("python", mode="quick")
    if result['success'] and result['processes']:
        proc = result['processes'][0]
        if 'memory_human' in proc:
            print(f"   [OK] Memory shown as: {proc['memory_human']} (was {proc['memory_mb']} MB)")
        else:
            print(f"   [FAIL] memory_human field not found")
    print()
    
    # Test 2: Dry run for kill_process
    print("2. Testing dry-run for kill_process...")
    if result['success'] and result['processes']:
        test_pid = result['processes'][0]['pid']
        dry_result = await pm.kill_process(test_pid, dry_run=True)
        if dry_result.get('dry_run'):
            print(f"   [OK] Dry run successful: {dry_result['message']}")
        else:
            print(f"   [FAIL] Dry run flag not working")
    print()
    
    # Test 3: Dry run for kill_process_tree
    print("3. Testing dry-run for kill_process_tree...")
    if result['success'] and result['processes']:
        test_pid = result['processes'][0]['pid']
        dry_result = await pm.kill_process_tree(test_pid, dry_run=True)
        if dry_result.get('dry_run'):
            print(f"   [OK] Dry run successful: Would kill {dry_result.get('process_count', 0)} processes")
        else:
            print(f"   [FAIL] Dry run flag not working")
    print()
    
    # Test 4: Check version
    print("4. Checking version...")
    list_result = await pm.list_allowed_commands()
    version = list_result.get('version', 'unknown')
    print(f"   Version: {version}")
    if '3.2' in version:
        print(f"   [OK] Version 3.2 confirmed!")
    else:
        print(f"   [FAIL] Version mismatch")
    print()
    
    print("=== Test Complete ===")
    print("\nNote: Command aliases (ps, kill, netstat) are handled in the MCP layer")
    print("They will work when called through Claude Desktop after restart")

if __name__ == "__main__":
    asyncio.run(test_v32_features())
