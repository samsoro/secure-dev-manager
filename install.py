#!/usr/bin/env python3
"""
Quick Installation Helper for Secure Dev Manager
Installs dependencies and sets up Claude Desktop configuration
"""

import subprocess
import sys
import json
import os
from pathlib import Path

def install_dependencies():
    """Install required packages"""
    print("=" * 60)
    print("Secure Dev Manager - Installation Helper")
    print("=" * 60)
    print("\n📦 Installing required dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Core dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    # Optional pywin32 for enhanced features
    if sys.platform == "win32":
        print("\n📋 Optional: pywin32 provides enhanced orphan prevention")
        print("   This prevents zombie processes more reliably.")
        response = input("   Install pywin32? (recommended) [y/N]: ").lower().strip()
        if response == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
                print("✅ pywin32 installed successfully!")
            except subprocess.CalledProcessError:
                print("⚠️  pywin32 installation failed, continuing without it...")
    
    return True

def setup_claude_config():
    """Add to Claude Desktop configuration"""
    print("\n🔧 Setting up Claude Desktop configuration...")
    
    if sys.platform != "win32":
        print("⚠️  Not on Windows - please manually configure Claude Desktop")
        return
    
    try:
        config_dir = Path(os.environ.get('APPDATA', '')) / 'Claude'
        config_path = config_dir / 'claude_desktop_config.json'
        
        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing config or create new
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"📄 Found existing config at: {config_path}")
        else:
            config = {"mcpServers": {}}
            print(f"📄 Creating new config at: {config_path}")
        
        # Ensure mcpServers exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Add our server configuration
        server_path = str(Path(__file__).parent / 'secure_dev_manager.py').replace('\\', '\\\\')
        
        config["mcpServers"]["secure-dev"] = {
            "command": "python",
            "args": [server_path]
        }
        
        # Write updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Claude Desktop configuration updated!")
        print(f"   Config location: {config_path}")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not automatically configure Claude Desktop: {e}")
        print("\n📝 Manual configuration needed:")
        print(f"   Add this to your claude_desktop_config.json:")
        print(f'   "secure-dev": {{')
        print(f'     "command": "python",')
        print(f'     "args": ["{Path(__file__).parent / "secure_dev_manager.py"}"]')
        print(f'   }}')
        return False

def verify_installation():
    """Quick verification of the installation"""
    print("\n🔍 Verifying installation...")
    
    try:
        import psutil
        print("✅ psutil is installed and working")
        
        # Check if pywin32 is available
        try:
            import win32job
            print("✅ pywin32 is installed (enhanced features enabled)")
        except ImportError:
            print("📋 pywin32 not installed (basic features only)")
        
        # Check if main script is accessible
        script_path = Path(__file__).parent / 'secure_dev_manager.py'
        if script_path.exists():
            print(f"✅ Main script found at: {script_path}")
        else:
            print(f"❌ Main script not found at: {script_path}")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main installation process"""
    # Handle --help flag
    if '--help' in sys.argv:
        print("Secure Dev Manager Installation Helper")
        print("Usage: python install.py")
        print("\nThis script will:")
        print("  - Install required dependencies (psutil)")
        print("  - Optionally install pywin32 for enhanced features")
        print("  - Configure Claude Desktop integration")
        return 0
    
    print("\n🚀 Welcome to Secure Dev Manager Installation!\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required (you have {sys.version})")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed - please check errors above")
        sys.exit(1)
    
    # Setup Claude config
    setup_claude_config()
    
    # Verify
    if verify_installation():
        print("\n" + "=" * 60)
        print("🎉 Installation Complete!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("   1. Restart Claude Desktop")
        print("   2. Type: @secure-dev-manager help")
        print("   3. Enjoy never having stuck ports again! 🚀")
        print("\n💡 Quick commands to try:")
        print("   @secure-dev-manager status     - See what's running")
        print("   @secure-dev-manager ps python  - Find Python processes")
        print("   @secure-dev-manager netstat    - Check dev ports")
    else:
        print("\n⚠️  Installation completed with warnings")
        print("   Please check the messages above")

if __name__ == "__main__":
    main()
