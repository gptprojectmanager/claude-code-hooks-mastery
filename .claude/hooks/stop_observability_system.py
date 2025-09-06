#!/usr/bin/env python3
"""
Automatic Observability System Stop Hook  
Stops the observability system when Claude Code sessions end
"""

import subprocess
import sys
import os
import signal
import json
import requests
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

def kill_process_group(pid):
    """Kill process and its children"""
    try:
        # Kill process group (includes children)
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        return True
    except:
        try:
            # Fallback to killing just the process
            os.kill(pid, signal.SIGTERM)
            return True
        except:
            return False

def check_system_running():
    """Check if observability system is running"""
    try:
        response = requests.get('http://localhost:4000/health', timeout=2)
        return response.status_code == 200
    except:
        return False

def stop_system():
    """Stop observability system processes"""
    script_dir = Path(__file__).parent.parent.parent
    pids_file = script_dir / '.claude' / 'observability_pids.json'
    
    # Check if PID file exists
    if not pids_file.exists():
        if check_system_running():
            log("⚠️  System running but no PID file found", 'YELLOW')
            # Try to kill by port
            try:
                # Kill processes using ports 4000 and 5173
                subprocess.run(['pkill', '-f', 'bun.*server.*dev'], capture_output=True)
                subprocess.run(['pkill', '-f', 'bun.*client.*dev'], capture_output=True)
                log("✅ Killed observability processes by pattern", 'GREEN')
            except:
                log("⚠️  Could not kill processes by pattern", 'YELLOW')
        else:
            log("✅ Observability system not running", 'GREEN')
        return True
    
    # Read PIDs from file
    try:
        with open(pids_file, 'r') as f:
            pids_data = json.load(f)
        
        server_pid = pids_data.get('server_pid')
        client_pid = pids_data.get('client_pid')
        
        log("🛑 Stopping observability system...", 'BLUE')
        
        # Stop server
        if server_pid:
            if kill_process_group(server_pid):
                log(f"✅ Stopped server (PID: {server_pid})", 'GREEN')
            else:
                log(f"⚠️  Could not stop server (PID: {server_pid})", 'YELLOW')
        
        # Stop client  
        if client_pid:
            if kill_process_group(client_pid):
                log(f"✅ Stopped client (PID: {client_pid})", 'GREEN')
            else:
                log(f"⚠️  Could not stop client (PID: {client_pid})", 'YELLOW')
        
        # Remove PID file
        pids_file.unlink()
        log("🗑️  Cleaned up PID file", 'GREEN')
        
        # Verify system is stopped
        import time
        time.sleep(1)  # Give processes time to stop
        
        if not check_system_running():
            log("✅ Observability system stopped successfully", 'GREEN')
        else:
            log("⚠️  System may still be running (manual cleanup may be needed)", 'YELLOW')
        
        return True
        
    except Exception as e:
        log(f"❌ Error reading PID file: {e}", 'RED')
        # Try cleanup anyway
        try:
            subprocess.run(['pkill', '-f', 'bun.*server.*dev'], capture_output=True)
            subprocess.run(['pkill', '-f', 'bun.*client.*dev'], capture_output=True)
            if pids_file.exists():
                pids_file.unlink()
            log("✅ Performed emergency cleanup", 'YELLOW')
        except:
            log("❌ Emergency cleanup failed", 'RED')
        return False

def main():
    """Main entry point"""
    try:
        # Only stop if system is actually running
        if not check_system_running():
            log("✅ Observability system not running", 'GREEN')
            # Clean up PID file if it exists
            script_dir = Path(__file__).parent.parent.parent
            pids_file = script_dir / '.claude' / 'observability_pids.json'
            if pids_file.exists():
                pids_file.unlink()
                log("🗑️  Cleaned up stale PID file", 'GREEN')
            return 0
        
        # Stop the system
        success = stop_system()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        log("⚠️  Stop interrupted", 'YELLOW')
        return 1
    except Exception as e:
        log(f"❌ Error: {e}", 'RED')
        return 1

if __name__ == "__main__":
    sys.exit(main())