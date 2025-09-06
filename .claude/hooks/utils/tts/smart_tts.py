#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

"""
Smart TTS Wrapper - Intelligent fallback between TTS services
Prioritizes working services and tracks failures to avoid repeated attempts
Now with macOS Say premium voice support as primary free option
ElevenLabs has been completely removed from the system
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Cache file to track service failures
CACHE_FILE = Path.home() / ".cache" / "claude-code" / "tts_status.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_service_status():
    """Load cached service status"""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_service_status(status):
    """Save service status to cache"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(status, f, indent=2)
    except:
        pass

def is_service_blocked(service_name, status):
    """Check if service is temporarily blocked due to recent failures"""
    if service_name not in status:
        return False
    
    last_failure = status[service_name].get('last_failure')
    if not last_failure:
        return False
    
    # For other failures, block for 1 hour
    failure_time = datetime.fromisoformat(last_failure)
    if datetime.now() - failure_time < timedelta(hours=1):
        return True
    
    return False

def mark_service_failure(service_name, reason="unknown"):
    """Mark a service as failed"""
    status = load_service_status()
    status[service_name] = {
        'last_failure': datetime.now().isoformat(),
        'reason': reason
    }
    save_service_status(status)

def mark_service_success(service_name):
    """Mark a service as successful"""
    status = load_service_status()
    if service_name in status:
        del status[service_name]
    save_service_status(status)

def try_tts_service(script_path, text, service_name):
    """Try to use a specific TTS service"""
    try:
        # Use shorter timeout for faster fallback
        timeout = 5 if service_name not in ['pyttsx3', 'macos_say'] else 8
        
        result = subprocess.run(
            ["uv", "run", str(script_path), text],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Check for successful playback
        if "Playback complete" in result.stdout or "Speaking..." in result.stdout or result.returncode == 0:
            mark_service_success(service_name)
            return True
        
        return False
            
    except subprocess.TimeoutExpired:
        # Don't mark as failure for timeout - might be temporary
        return False
    except Exception:
        return False

def main():
    """Main TTS function with intelligent fallback - ElevenLabs removed"""
    if len(sys.argv) < 2:
        sys.exit(0)
    
    text = sys.argv[1]
    script_dir = Path(__file__).parent
    status = load_service_status()
    
    # Clean up any ElevenLabs entries from status cache
    if 'elevenlabs' in status:
        del status['elevenlabs']
        save_service_status(status)
    
    # Define services in priority order (ElevenLabs removed)
    services = []
    
    # PRIORITY 1: macOS Say (Premium Free) - Always try first on macOS
    if sys.platform == "darwin":
        macos_script = script_dir / "macos_say_tts.py"
        if macos_script.exists():
            services.append(('macos_say', macos_script))
            print("🎯 Using macOS Say premium voice (free, high quality)")
    
    # PRIORITY 2: OpenAI TTS if available
    if not is_service_blocked('openai', status):
        if os.getenv('OPENAI_API_KEY'):
            openai_script = script_dir / "openai_tts.py"
            if openai_script.exists():
                services.append(('openai', openai_script))
    
    # PRIORITY 3: Always add pyttsx3 as final fallback (no API needed)
    pyttsx3_script = script_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        services.append(('pyttsx3', pyttsx3_script))
    
    # If no services available, exit silently
    if not services:
        sys.exit(0)
    
    # Try each service in order
    for service_name, script_path in services:
        if try_tts_service(script_path, text, service_name):
            sys.exit(0)
    
    # All services failed - silent failure
    sys.exit(0)

if __name__ == "__main__":
    main()