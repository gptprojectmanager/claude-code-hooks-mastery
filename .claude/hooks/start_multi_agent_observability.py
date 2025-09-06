#!/usr/bin/env -S uv run --project /Users/sam/claude-code-hooks-mastery python
"""
Multi-Agent Observability System Startup Hook
Starts the correct observability system from /Users/sam/claude-code-hooks-multi-agent-observability
"""

import os
import subprocess
import sys
import time
import requests
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

# Target observability system path
OBSERVABILITY_ROOT = Path("/Users/sam/claude-code-hooks-multi-agent-observability")

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

def verify_observability_project():
    """Verify observability project structure"""
    if not OBSERVABILITY_ROOT.exists():
        log(f"❌ Observability project not found: {OBSERVABILITY_ROOT}", 'RED')
        return False
    
    server_dir = OBSERVABILITY_ROOT / 'apps' / 'server'
    client_dir = OBSERVABILITY_ROOT / 'apps' / 'client'
    
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
    
    log("✅ Multi-agent observability project validated", 'GREEN')
    return True

def start_system_background():
    """Start observability system in background"""
    # Start server
    log("🔌 Starting multi-agent observability server...", 'BLUE')
    server_dir = OBSERVABILITY_ROOT / 'apps' / 'server'
    
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
    
    # Start client (try port 5173 first, fallback to 5174)
    log("🖥️  Starting multi-agent observability client...", 'BLUE')  
    client_dir = OBSERVABILITY_ROOT / 'apps' / 'client'
    client_port = 5173
    
    # Check if port 5173 is available, otherwise try 5174
    if check_port(5173):
        client_port = 5174
        log("⚠️  Port 5173 in use, using port 5174", 'YELLOW')
    
    try:
        # Set port via environment variable if not default
        env = os.environ.copy()
        if client_port != 5173:
            env['PORT'] = str(client_port)
            
        client_proc = subprocess.Popen(
            ['bun', 'run', 'dev'],
            cwd=client_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,  # Create new process group
            env=env
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
            response = requests.get(f'http://localhost:{client_port}', timeout=1)
            if response.status_code == 200:
                log("✅ Client ready!", 'GREEN')
                break
        except:
            pass
        time.sleep(0.5)
    else:
        log("⚠️  Client may not be ready yet (continuing anyway)", 'YELLOW')
    
    # Store PIDs for cleanup in the hooks mastery project
    pids_file = Path(__file__).parent.parent / 'observability_pids.json'
    pids_data = {
        'server_pid': server_proc.pid,
        'client_pid': client_proc.pid,
        'client_port': client_port,
        'started_at': time.time(),
        'project': str(OBSERVABILITY_ROOT)
    }
    
    with open(pids_file, 'w') as f:
        json.dump(pids_data, f, indent=2)
    
    log("🚀 Multi-agent observability system started successfully!", 'GREEN')
    log(f"🖥️  Dashboard: http://localhost:{client_port}", 'BLUE')
    log(f"🔌 API: http://localhost:4000", 'BLUE')
    log(f"📡 WebSocket: ws://localhost:4000/stream", 'BLUE')
    
    return True

def main():
    """Main entry point"""
    try:
        # Check if already running
        if is_system_running():
            log("✅ Multi-agent observability system already running", 'GREEN')
            return 0
        
        # Check dependencies
        if not check_dependencies():
            log("❌ Missing dependencies", 'RED')
            return 1
        
        # Verify observability project structure
        if not verify_observability_project():
            log("❌ Multi-agent observability project not available", 'RED')
            return 1
        
        # Check if ports are available
        if check_port(4000):
            log("⚠️  Port 4000 is in use (non-observability process)", 'YELLOW')
            return 1
        
        # Start system in background
        log("🚀 Auto-starting multi-agent observability system...", 'BLUE')
        success = start_system_background()
        
        if success:
            return 0
        else:
            log("❌ Failed to start multi-agent observability system", 'RED')
            return 1
            
    except KeyboardInterrupt:
        log("⚠️  Startup interrupted", 'YELLOW')
        return 1
    except Exception as e:
        log(f"❌ Error: {e}", 'RED')
        return 1

if __name__ == "__main__":
    sys.exit(main())