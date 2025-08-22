#!/usr/bin/env python3
"""
Test script to verify Render deployment configuration
"""

import sys
import os

def check_files():
    """Check if all required files exist"""
    required_files = [
        'Procfile',
        'requirements-render.txt', 
        'runtime.txt',
        'backend_simple.py',
        'render.yaml'
    ]
    
    print("🔍 Checking required deployment files...")
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - Found")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_procfile():
    """Check Procfile configuration"""
    print("\n📋 Checking Procfile...")
    try:
        with open('Procfile', 'r') as f:
            content = f.read().strip()
            print(f"Content: {content}")
            
            if 'backend_simple.py' in content:
                print("✅ Procfile uses backend_simple.py")
                return True
            else:
                print("❌ Procfile doesn't use backend_simple.py")
                return False
    except Exception as e:
        print(f"❌ Error reading Procfile: {e}")
        return False

def check_requirements():
    """Check requirements file"""
    print("\n📦 Checking requirements-render.txt...")
    try:
        with open('requirements-render.txt', 'r') as f:
            content = f.read().strip()
            lines = content.split('\n')
            
            print(f"Dependencies ({len(lines)}):")
            for line in lines:
                if line.strip():
                    print(f"  - {line}")
            
            # Check for problematic packages
            problematic = ['pandas', 'scikit-learn', 'tensorflow', 'torch']
            has_problems = any(pkg in content for pkg in problematic)
            
            if has_problems:
                print("⚠️  Contains heavy dependencies that may cause build issues")
                return False
            else:
                print("✅ Minimal dependencies - should build successfully")
                return True
                
    except Exception as e:
        print(f"❌ Error reading requirements: {e}")
        return False

def check_backend():
    """Check backend file"""
    print("\n🔧 Checking backend_simple.py...")
    try:
        with open('backend_simple.py', 'r') as f:
            content = f.read()
            
            # Check for problematic imports
            problematic_imports = [
                'pandas', 'sklearn', 'tensorflow', 'torch',
                'numpy', 'joblib'
            ]
            
            has_problems = any(f"import {pkg}" in content for pkg in problematic_imports)
            
            if has_problems:
                print("⚠️  Contains problematic imports")
                return False
            else:
                print("✅ Clean imports - should work on Render")
                
            # Check for required endpoints
            endpoints = ['/health', '/patients', '/alerts/active']
            missing_endpoints = []
            
            for endpoint in endpoints:
                if endpoint in content:
                    print(f"✅ {endpoint} endpoint found")
                else:
                    missing_endpoints.append(endpoint)
                    print(f"❌ {endpoint} endpoint missing")
            
            return len(missing_endpoints) == 0
                
    except Exception as e:
        print(f"❌ Error reading backend: {e}")
        return False

def main():
    print("🚀 Render Deployment Configuration Test")
    print("=" * 50)
    
    checks = [
        check_files(),
        check_procfile(), 
        check_requirements(),
        check_backend()
    ]
    
    success_count = sum(checks)
    total_checks = len(checks)
    
    print(f"\n📊 Results: {success_count}/{total_checks} checks passed")
    
    if success_count == total_checks:
        print("🎉 All checks passed! Configuration should work on Render.")
        print("\n💡 If deployment still fails, try:")
        print("  1. Check Render build logs for specific errors")
        print("  2. Manually trigger a redeploy in Render dashboard")
        print("  3. Verify environment variables are set correctly")
    else:
        print("⚠️  Some issues found. Fix them before deploying.")
        
    print(f"\n🔗 Your GitHub repo: https://github.com/Parthchavann/early_warning_system")

if __name__ == "__main__":
    main()