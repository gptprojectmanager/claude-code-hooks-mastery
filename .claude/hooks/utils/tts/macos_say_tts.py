#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
macOS Say TTS - Premium quality voices using built-in macOS speech synthesis
Uses macOS 'say' command with premium neural voices for high-quality output
"""

import sys
import subprocess
import random
import os
from pathlib import Path

def get_best_voices():
    """Get list of best macOS voices for English"""
    premium_voices = [
        # Premium Neural Voices (macOS 13+)
        "Samantha",  # Premium US female voice - very natural
        "Karen",     # Australian female - clear and professional  
        "Daniel",    # British male - professional
        "Fiona",     # Scottish female - pleasant accent
        "Alex",      # Default US male - reliable fallback
        "Victoria",  # US female - clear
        "Allison",   # US female - professional
        "Ava",       # US female - modern
    ]
    
    # Check which voices are actually available
    try:
        result = subprocess.run(
            ["say", "-v", "?"],
            capture_output=True,
            text=True,
            timeout=2
        )
        available = result.stdout
        
        # Filter to only available voices
        available_premium = []
        for voice in premium_voices:
            if voice in available:
                available_premium.append(voice)
        
        return available_premium if available_premium else ["Alex"]  # Alex is always available
    except:
        return ["Alex"]  # Default fallback

def speak_with_say(text, voice=None):
    """Use macOS say command to speak text"""
    try:
        # Get available premium voices
        voices = get_best_voices()
        
        # Select voice
        if not voice:
            # Prefer Samantha (most natural) if available
            if "Samantha" in voices:
                voice = "Samantha"
            # Otherwise pick a random premium voice for variety
            else:
                voice = random.choice(voices)
        
        print(f"🎭 Using macOS voice: {voice}")
        print(f"🎯 Text: {text}")
        print("🔊 Speaking...")
        
        # Use say command with selected voice
        # -r flag sets speech rate (default is 200, we use 180 for clarity)
        result = subprocess.run(
            ["say", "-v", voice, "-r", "180", text],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Playback complete!")
            return True
        else:
            print(f"⚠️ Say command failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ Speech synthesis timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """
    macOS Say TTS Script
    
    Uses macOS built-in 'say' command for premium quality text-to-speech.
    No API keys required, completely free, premium neural voices.
    
    Usage:
    - ./macos_say_tts.py                    # Uses default text
    - ./macos_say_tts.py "Your custom text" # Uses provided text
    
    Features:
    - Premium neural voices (Samantha, Karen, Daniel, etc.)
    - No API key required - completely free
    - High-quality natural speech synthesis
    - Multiple accent options
    - Immediate audio playback
    """
    
    print("🎙️  macOS Say TTS (Premium Free)")
    print("=" * 35)
    
    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ Error: This script only works on macOS")
        sys.exit(1)
    
    # Get text from command line argument or use default
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])  # Join all arguments as text
    else:
        # Default completion messages
        completion_messages = [
            "Work complete!",
            "All done!",
            "Task finished successfully!",
            "Job complete!",
            "Ready for next task!",
            "Operation successful!"
        ]
        text = random.choice(completion_messages)
    
    # Speak the text
    success = speak_with_say(text)
    
    if not success:
        # Try fallback with default voice
        print("🔄 Retrying with default voice...")
        success = speak_with_say(text, "Alex")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()