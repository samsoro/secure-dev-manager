#!/usr/bin/env python3
"""Quick push for CI fixes"""
import subprocess
import os

os.chdir(r"C:\Users\Bizon\AI-Projects\mcp-infrastructure\servers\secure-dev")

commands = [
    'git add .',
    'git commit -m "Fix CI workflow - add basic tests and handle --help flag"',
    'git push'
]

for cmd in commands:
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print("Success!")

print("\nCI fixes pushed! Check GitHub Actions in a minute.")
