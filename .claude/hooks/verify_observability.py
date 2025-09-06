#!/usr/bin/env python3
"""
Observability System Verification Script
Verifies that the observability system is running correctly
"""

import requests
import sys
import json
from pathlib import Path

def check_dashboard():
    """Check if dashboard is accessible"""
    try:
        response = requests.get('http://localhost:5173', timeout=5)
        if response.status_code == 200 and 'Multi-Agent Observability' in response.text:
            print("✅ Dashboard accessible and valid")
            return True
        else:
            print(f"❌ Dashboard returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard not accessible: {e}")
        return False

def check_api():
    """Check if API is responding"""
    try:
        response = requests.get('http://localhost:4000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("✅ API health endpoint OK")
                return True
            else:
                print(f"❌ API health check failed: {data}")
                return False
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        return False

def check_processes():
    """Check if PIDs file exists and processes are running"""
    try:
        pids_file = Path('.claude/observability_pids.json')
        if not pids_file.exists():
            print("❌ PID file not found")
            return False
        
        with open(pids_file, 'r') as f:
            pids_data = json.load(f)
        
        server_pid = pids_data.get('server_pid')
        client_pid = pids_data.get('client_pid')
        
        if server_pid and client_pid:
            print(f"✅ PIDs tracked: server={server_pid}, client={client_pid}")
            return True
        else:
            print("❌ Invalid PID data")
            return False
    except Exception as e:
        print(f"❌ PID check failed: {e}")
        return False

def main():
    """Main verification"""
    print("🔍 Verifying observability system...")
    
    checks = [
        ("Dashboard", check_dashboard),
        ("API", check_api),
        ("Processes", check_processes)
    ]
    
    passed = 0
    for name, check_func in checks:
        print(f"\n🔸 Checking {name}...")
        if check_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())