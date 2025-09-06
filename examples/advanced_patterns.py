"""
Advanced usage patterns for secure-dev-manager
Demonstrates performance features and best practices
"""

import asyncio
from datetime import datetime

# Example 1: Efficient process searching
async def efficient_search_example():
    """Shows how to search efficiently"""
    
    # Good: Specific searches are fast
    await find_process("python")      # ~0.08s
    await find_process("node")        # ~0.08s
    await find_process("chrome")      # ~0.10s
    
    # Good: 2-3 character searches work well
    await find_process("py")          # ~0.06s
    await find_process("git")         # ~0.08s
    
    # Bad: Single character searches are blocked
    # await find_process("e")  # Error: Too short
    
    # Bad: Including args makes it slower
    # await find_process("python", include_args=True)  # Slower

# Example 2: Performance monitoring
async def monitor_performance():
    """Check performance of operations"""
    
    # All operations return elapsed_seconds
    result = await find_process("python")
    print(f"Search took: {result['elapsed_seconds']:.3f}s")
    
    # Debug info shows what happened
    print(f"Scanned: {result['debug_info']['total_scanned']} processes")
    print(f"Found: {result['debug_info']['matches_found']} matches")
    print(f"Cache hits: {result['debug_info']['cache_hits']}")

# Example 3: Working with protected processes
async def handle_protected_processes():
    """Understand process protection"""
    
    result = await find_process("python")
    for proc in result['processes']:
        if proc['protected']:
            print(f"PID {proc['pid']} is protected (MCP infrastructure)")
            # Can't kill this one
        else:
            print(f"PID {proc['pid']} can be terminated")
            # Safe to kill if needed

# Example 4: Port management workflow
async def manage_dev_server():
    """Common workflow for dev servers"""
    
    # Check what's using port 8000
    ports = await check_ports(8000)
    if ports['ports'][8000]['status'] == 'active':
        process = ports['ports'][8000]['process']
        if process:
            print(f"Port 8000 used by PID {process['pid']}")
            
            # Check if we can kill it
            kill_result = await kill_process(process['pid'])
            if kill_result['success']:
                print("Port 8000 is now free!")
            else:
                print(f"Can't kill: {kill_result['error']}")
                if kill_result.get('developer_message'):
                    print(kill_result['developer_message'])

# Example 5: Batch operations with caching
async def batch_operations():
    """Cache makes repeated operations fast"""
    
    # First call populates cache
    await find_process("python")  # ~0.08s
    
    # Subsequent calls within 10s use cache
    await find_process("python")  # Much faster (cache hit)
    await find_process("python")  # Still fast
    
    # After 10 seconds, cache refreshes
    await asyncio.sleep(11)
    await find_process("python")  # Fresh scan

# Example 6: Virtual environment aware execution
async def venv_aware_execution():
    """Commands auto-detect virtual environments"""
    
    # In a project directory with .venv
    result = await execute_command(
        "python manage.py runserver",
        cwd="C:/Projects/my-django-app"
    )
    # Automatically uses C:/Projects/my-django-app/.venv
    
    # Known project venvs are also detected
    result = await execute_command(
        "python app.py",
        cwd="C:/Users/Bizon/AI-Projects/portfolio-analysis"
    )
    # Uses portfolio-analysis/.venv automatically

# Example 7: Server lifecycle management
async def manage_server_lifecycle():
    """Start, monitor, and stop servers"""
    
    # Start a server in background
    result = await execute_command(
        "python app.py",
        cwd="C:/Projects/my-app",
        background=True
    )
    server_pid = result['pid']
    print(f"Server started with PID {server_pid}")
    
    # Check server status
    status = await get_server_status()
    for server in status['managed_servers']:
        print(f"Server {server['pid']}: {server['status']}")
        print(f"  Memory: {server['memory_mb']}MB")
    
    # Stop the server
    await kill_process(server_pid)
    print("Server stopped")

# Example 8: Error handling with developer hints
async def handle_errors_gracefully():
    """Tool provides helpful error messages"""
    
    # Try to kill a protected process
    result = await kill_process(1234)  # Some MCP process
    if not result['success']:
        print(f"Error: {result['error']}")
        
        # Developer hints explain what to do
        if 'developer_message' in result:
            print("\nWhat to do:")
            print(result['developer_message'])
        
        if 'developer_hint' in result:
            print("\nHint:", result['developer_hint'])

# Example 9: Performance-safe patterns
async def performance_patterns():
    """Patterns that maintain good performance"""
    
    # ✅ Good: Specific searches
    await find_process("python")
    await find_process("node")
    
    # ✅ Good: Check specific port
    await check_ports(8000)
    
    # ✅ Good: Use cache for repeated operations
    for _ in range(5):
        await find_process("python")  # Uses cache after first
    
    # ❌ Bad: Too broad searches
    # await find_process("e")  # Would match everything
    
    # ❌ Bad: Including args unnecessarily
    # await find_process("python", include_args=True)  # Slower
    
    # ❌ Bad: Checking all ports when you need one
    # await check_ports()  # Checks all 6 ports

# Example 10: Production monitoring
async def production_monitoring():
    """Monitor system health efficiently"""
    
    while True:
        # Quick health check
        start = datetime.now()
        
        # Check critical processes
        python_procs = await find_process("python")
        if python_procs['count'] < 2:
            print("WARNING: MCP servers might be down!")
        
        # Check critical ports
        ports = await check_ports()
        active_ports = [p for p, info in ports['ports'].items() 
                       if info['status'] == 'active']
        
        # Performance check
        elapsed = (datetime.now() - start).total_seconds()
        if elapsed > 1.0:
            print(f"WARNING: Health check slow ({elapsed:.2f}s)")
        
        # Wait before next check
        await asyncio.sleep(30)

if __name__ == "__main__":
    # Example usage
    asyncio.run(efficient_search_example())
