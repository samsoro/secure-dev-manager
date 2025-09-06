#!/usr/bin/env python3
"""Create and push version tag for v3.2.0"""
import subprocess
import os

def run_command(cmd):
    """Run a command"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Running: {cmd}")
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Failed: {e}")
        return False

# Change to project directory
os.chdir(r"C:\Users\Bizon\AI-Projects\mcp-infrastructure\servers\secure-dev")

# Create annotated tag
print("Creating version tag v3.2.0...")
if run_command('git tag -a v3.2.0 -m "Version 3.2.0 - The Alias Update"'):
    print("Tag created successfully!")
else:
    print("Tag might already exist, continuing...")

# Push tag to GitHub
print("\nPushing tag to GitHub...")
if run_command("git push origin v3.2.0"):
    print("Tag pushed successfully!")
else:
    print("Tag push might have failed - check manually")

print("\nDone! Check https://github.com/samsoro/secure-dev-manager/releases")
