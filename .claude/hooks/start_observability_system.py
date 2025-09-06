#!/usr/bin/env python3
"""
Automatic Observability System Startup Hook
Starts the observability system in background for Claude Code sessions
"""

import subprocess
import sys
import time
import requests
import os
import signal
import json
from pathlib import Path

# Colors for output
COLORS = {
    'GREEN': '\033[0;32m',
    'YELLOW': '\033[0;33m', 
    'BLUE': '\033[0;34m',
    'RED': '\033[0;31m',
    'NC': '\033[0m'  # No Color
}

def log(message, color='NC'):
    """Log message with color"""
    print(f"{COLORS[color]}{message}{COLORS['NC']}", flush=True)

def check_port(port):
    """Check if port is in use"""
    try:
        result = subprocess.run(['lsof', '-Pi', f':{port}', '-sTCP:LISTEN', '-t'], 
                               capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def is_system_running():
    """Check if observability system is already running"""
    try:
        # Check server health endpoint
        response = requests.get('http://localhost:4000/health', timeout=2)
        return response.status_code == 200
    except:
        return False

def check_dependencies():
    """Check if bun is available"""
    try:
        result = subprocess.run(['bun', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            log(f"✅ Bun version {result.stdout.strip()} available", 'GREEN')
            return True
        else:
            log("❌ Bun not available", 'RED')
            return False
    except:
        log("❌ Bun not found in PATH", 'RED')
        return False

def verify_project_structure():
    """Verify app directories exist"""
    script_dir = Path(__file__).parent.parent.parent
    server_dir = script_dir / 'apps' / 'server'
    client_dir = script_dir / 'apps' / 'client'
    
    if not server_dir.exists():
        log(f"❌ Server directory not found: {server_dir}", 'RED')
        return False
    
    if not client_dir.exists():
        log(f"❌ Client directory not found: {client_dir}", 'RED')
        return False
    
    # Check package.json files
    server_pkg = server_dir / 'package.json'
    client_pkg = client_dir / 'package.json'
    
    if not server_pkg.exists():
        log(f"❌ Server package.json not found", 'RED')
        return False
        
    if not client_pkg.exists():
        log(f"❌ Client package.json not found", 'RED')
        return False
    
    log("✅ Project structure validated", 'GREEN')
    return True

def start_system_background():
    """Start observability system in background"""
    # Get project root
    script_dir = Path(__file__).parent.parent.parent
    
    # Start server
    log("🔌 Starting observability server...", 'BLUE')
    server_dir = script_dir / 'apps' / 'server'
    
    try:
        server_proc = subprocess.Popen(
            ['bun', 'run', 'dev'],
            cwd=server_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid  # Create new process group
        )
    except Exception as e:
        log(f"❌ Failed to start server: {e}", 'RED')
        return False
    
    # Wait for server to be ready (max 15 seconds)
    log("⏳ Waiting for server to start...", 'YELLOW')
    for i in range(30):  # 30 * 0.5 = 15 seconds max
        try:
            response = requests.get('http://localhost:4000/health', timeout=1)
            if response.status_code == 200:
                log("✅ Server ready!", 'GREEN')
                break
        except:
            pass
        time.sleep(0.5)
    else:
        log("❌ Server failed to start within timeout", 'RED')
        try:
            os.killpg(os.getpgid(server_proc.pid), signal.SIGTERM)
        except:
            pass
        return False
    
    # Start client
    log("🖥️  Starting observability client...", 'BLUE')  
    client_dir = script_dir / 'apps' / 'client'
    
    try:
        client_proc = subprocess.Popen(
            ['bun', 'run', 'dev'],
            cwd=client_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid  # Create new process group
        )
    except Exception as e:
        log(f"❌ Failed to start client: {e}", 'RED')
        try:
            os.killpg(os.getpgid(server_proc.pid), signal.SIGTERM)
        except:
            pass
        return False
    
    # Wait for client to be ready (max 15 seconds)
    log("⏳ Waiting for client to start...", 'YELLOW')
    for i in range(30):  # 30 * 0.5 = 15 seconds max
        try:
            response = requests.get('http://localhost:5173', timeout=1)
            if response.status_code == 200:
                log("✅ Client ready!", 'GREEN')
                break
        except:
            pass
        time.sleep(0.5)
    else:
        log("⚠️  Client may not be ready yet (continuing anyway)", 'YELLOW')
    
    # Store PIDs for cleanup
    pids_file = script_dir / '.claude' / 'observability_pids.json'
    pids_data = {
        'server_pid': server_proc.pid,
        'client_pid': client_proc.pid,
        'started_at': time.time()
    }
    
    with open(pids_file, 'w') as f:
        json.dump(pids_data, f, indent=2)
    
    log("🚀 Observability system started successfully!", 'GREEN')
    log(f"🖥️  Dashboard: http://localhost:5173", 'BLUE')
    log(f"🔌 API: http://localhost:4000", 'BLUE')
    log(f"📡 WebSocket: ws://localhost:4000/stream", 'BLUE')
    
    return True

def main():
    """Main entry point"""
    try:
        # Check if already running
        if is_system_running():
            log("✅ Observability system already running", 'GREEN')
            return 0
        
        # Check dependencies
        if not check_dependencies():
            log("❌ Missing dependencies", 'RED')
            return 1
        
        # Verify project structure
        if not verify_project_structure():
            log("❌ Project structure invalid", 'RED')
            return 1
        
        # Check if ports are available
        if check_port(4000):
            log("⚠️  Port 4000 is in use (non-observability process)", 'YELLOW')
            return 1
            
        if check_port(5173):
            log("⚠️  Port 5173 is in use (non-observability process)", 'YELLOW')
            return 1
        
        # Start system in background
        log("🚀 Auto-starting observability system...", 'BLUE')
        success = start_system_background()
        
        if success:
            # Initialize observability integration
            script_dir = Path(__file__).parent.parent.parent
            integration_script = script_dir / '.claude' / 'scripts' / 'observability-integration.js'
            
            if integration_script.exists():
                log("🔧 Initializing observability integration...", 'BLUE')
                try:
                    result = subprocess.run(
                        ['node', str(integration_script), 'test'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        log("✅ Observability integration initialized", 'GREEN')
                    else:
                        log("⚠️  Integration test completed with warnings", 'YELLOW')
                except:
                    log("⚠️  Integration test skipped (timeout/error)", 'YELLOW')
            
            return 0
        else:
            log("❌ Failed to start observability system", 'RED')
            return 1
            
    except KeyboardInterrupt:
        log("⚠️  Startup interrupted", 'YELLOW')
        return 1
    except Exception as e:
        log(f"❌ Error: {e}", 'RED')
        return 1

if __name__ == "__main__":
    sys.exit(main())