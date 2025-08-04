# start.py
import sys
import subprocess
import os


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 13:
        print("⚠️  Warning: Python 3.13+ detected. Some dependencies may have compatibility issues.")
        print("💡 Recommended: Use Python 3.11 or 3.12 for best compatibility.")

    return True


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True


def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    try:
        # Import here to avoid early import issues
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try running: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False


if __name__ == "__main__":
    print("🏗️  Cap Table Management System - Backend")
    print("=" * 50)

    if not check_python_version():
        sys.exit(1)

    # Check if we need to install dependencies
    try:
        import fastapi
        import sqlalchemy
        import uvicorn

        print("✅ Dependencies already installed")
    except ImportError:
        if not install_dependencies():
            sys.exit(1)

    start_server()