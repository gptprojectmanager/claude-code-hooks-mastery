#!/usr/bin/env python3
"""
Complete Multi-Agent TTS System Test
Tests both ElevenLabs and pyttsx3 TTS with different agents
"""

import subprocess
import time
import os

def test_tts_system(tts_script, text, description):
    """Test a TTS system"""
    print(f"\n🎤 {description}")
    print("-" * 50)
    
    try:
        # Set PATH for ElevenLabs (includes ffmpeg)
        env = os.environ.copy()
        env["PATH"] = "/opt/local/bin:" + env.get("PATH", "")
        
        result = subprocess.run([
            "python3", tts_script, text
        ], capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🎭 MULTI-AGENT TTS SYSTEM TEST")
    print("=" * 60)
    print("Testing both ElevenLabs (female voice) and pyttsx3 (local)")
    print("Simulating multi-agent workflow with TTS notifications")
    
    # Test scenarios
    tests = [
        {
            "script": ".claude/hooks/utils/tts/elevenlabs_tts.py",
            "text": "Ciao! Sono l'agente Primary Manager. Ho delegato il task al Code Reviewer.",
            "description": "ElevenLabs TTS - Primary Manager Agent"
        },
        {
            "script": ".claude/hooks/utils/tts/pyttsx3_tts.py", 
            "text": "Code review completato con successo. Task restituito al manager.",
            "description": "pyttsx3 TTS - Code Reviewer Agent"
        },
        {
            "script": ".claude/hooks/utils/tts/elevenlabs_tts.py",
            "text": "Perfetto! Il sistema multi-agente con TTS è completamente funzionante.",
            "description": "ElevenLabs TTS - System Completion"
        }
    ]
    
    successful_tests = 0
    total_tests = len(tests)
    
    for i, test in enumerate(tests, 1):
        print(f"\n🧪 Test {i}/{total_tests}")
        if test_tts_system(test["script"], test["text"], test["description"]):
            successful_tests += 1
        
        # Small delay between tests
        if i < total_tests:
            time.sleep(2)
    
    # Results
    print(f"\n📊 RISULTATI FINALI")
    print("=" * 40)
    print(f"✅ Test riusciti: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 Sistema Multi-Agente TTS completamente funzionante!")
        print("🔊 ElevenLabs: Voce femminile Rachel (premium)")
        print("🎤 pyttsx3: Voce locale femminile (offline)")
        print("📊 Dashboard observability: http://localhost:4000")
    else:
        print("⚠️  Alcuni test non sono riusciti")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    main()