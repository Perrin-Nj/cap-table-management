# test_runner_fixed.py (place this in project root, not in tests folder)
"""
Fixed test runner that handles path issues correctly
"""
import sys
import os
import subprocess
from pathlib import Path

def check_project_structure():
    """Check and display project structure"""
    print("🔍 Checking project structure...")
    print("-" * 40)
    
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Check for key files/directories
    key_items = [
        "app",
        "app/main.py", 
        "tests",
        "tests/basic_tests.py",
        "requirements.txt"
    ]
    
    for item in key_items:
        path = current_dir / item
        if path.exists():
            print(f"✅ {item} - exists")
        else:
            print(f"❌ {item} - missing")
    
    print(f"\nContents of current directory:")
    for item in current_dir.iterdir():
        print(f"  - {item.name} {'(dir)' if item.is_dir() else '(file)'}")
    
    if (current_dir / "app").exists():
        print(f"\nContents of app/ directory:")
        for item in (current_dir / "app").iterdir():
            print(f"  - {item.name}")

def run_direct_import_test():
    """Test direct import without pytest"""
    print("\n🧪 Testing direct imports...")
    print("-" * 40)
    
    try:
        # Add current directory to path
        current_dir = Path.cwd()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
            
        print(f"Python path includes: {current_dir}")
        
        # Test import
        print("Attempting to import app.main...")
        from app.main import app
        print("✅ Successfully imported app.main")
        
        # Test FastAPI client
        print("Creating test client...")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        print("✅ Successfully created test client")
        
        # Test health endpoint
        print("Testing health endpoint...")
        response = client.get("/health")
        print(f"Health endpoint returned: {response.status_code}")
        print(f"Response content: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Health endpoint working correctly")
            return True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                pass
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_pytest_tests():
    """Run pytest tests if direct import works"""
    print("\n🧪 Running pytest tests...")
    print("-" * 40)
    
    try:
        # Make sure we're in project root
        current_dir = Path.cwd()
        
        # Check if test file exists
        test_file = current_dir / "tests" / "basic_tests.py"
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        # Run pytest
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v", "-s", "--tb=short"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=current_dir, timeout=60)
        
        if result.returncode == 0:
            print("✅ Pytest tests passed!")
            return True
        else:
            print(f"❌ Pytest tests failed with code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Pytest execution failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Cap Table Test Runner")
    print("=" * 50)
    
    # Step 1: Check project structure
    check_project_structure()
    
    # Step 2: Test direct imports
    import_ok = run_direct_import_test()
    
    # Step 3: Run pytest if imports work
    if import_ok:
        pytest_ok = run_pytest_tests()
    else:
        print("\nSkipping pytest tests due to import issues")
        pytest_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    if import_ok and pytest_ok:
        print("🎉 All tests passed!")
    elif import_ok:
        print("⚠️  Direct imports work, but pytest has issues")
    else:
        print("❌ Basic imports failed - check your project structure")
    
    print("=" * 50)

if __name__ == "__main__":
    main()