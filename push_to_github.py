#!/usr/bin/env python3
"""
Push Secure Dev Manager changes to GitHub
Repository: https://github.com/samsoro/secure-dev-manager
"""
import subprocess
import os
import sys

def run_command(cmd, cwd=None):
    """Run a command and return its output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            encoding='utf-8'
        )
        print(f"$ {cmd}")
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Failed to run command: {e}", file=sys.stderr)
        return False, "", str(e)

def main():
    # Change to project directory
    project_root = r"C:\Users\Bizon\AI-Projects\mcp-infrastructure\servers\secure-dev"
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}\n")
    
    # The commit message for our release
    commit_message = """Release v3.2.0 - The Alias Update - Ready for public launch

Added essential files for open source release:
- requirements.txt for easy dependency management
- MIT LICENSE for open source distribution
- install.py for automated setup and configuration
- CONTRIBUTING.md for community contributors
- GitHub Actions CI workflow for testing
- RELEASE.md checklist for release process

The tool is now fully polished and ready for public release with:
- Comprehensive documentation (10+ guides)
- Professional test suite
- Easy installation process
- CI/CD pipeline
- Clear contribution guidelines"""
    
    # Check current git status
    print("=== Checking git status ===")
    success, stdout, stderr = run_command("git status --porcelain")
    if not success:
        print("Failed to check git status")
        return 1
    
    if stdout.strip():
        print("\n=== Changes to be committed ===")
        run_command("git status -s")
        
        # Show file count
        file_count = len(stdout.strip().split('\n'))
        print(f"\n[Files] {file_count} file(s) will be committed")
        
        # Add all changes
        print("\n=== Adding all changes ===")
        success, _, _ = run_command("git add -A")
        if not success:
            print("Failed to add changes")
            return 1
        
        # Commit the changes
        print("\n=== Committing changes ===")
        success, _, _ = run_command(f'git commit -m "{commit_message}"')
        if not success:
            print("Failed to commit changes")
            return 1
    else:
        print("No new changes to commit, proceeding to push...")
    
    # Push to GitHub
    print("\n=== Pushing to GitHub ===")
    success, stdout, stderr = run_command("git push origin main")
    if not success:
        # Try without specifying branch
        print("\n=== Trying simple push ===")
        success, _, _ = run_command("git push")
        if not success:
            print("\nFailed to push. You may need to run manually:")
            print("  git push origin main")
            return 1
    
    print("\n✅ Successfully pushed to GitHub!")
    print("\n🎉 Your tool is now on GitHub with all the polish!")
    print("\nNext steps:")
    print("1. Go to https://github.com/samsoro/secure-dev-manager")
    print("2. Make the repository PUBLIC in Settings")
    print("3. Create a Release from tag v3.2.0")
    print("4. Submit to MCP registries")
    print("\n🚀 Ready for launch!")
    
    # Create the version tag
    print("\n=== Creating version tag ===")
    run_command('git tag -a v3.2.0 -m "Version 3.2.0 - The Alias Update"')
    run_command("git push origin v3.2.0")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
