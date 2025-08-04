#!/usr/bin/env python3
"""
Test script to verify observability hooks are working
"""

import time
import os

def main():
    print("🧪 Testing Multi-Agent Observability Hooks")
    print("=" * 50)
    
    print("1. Creating test file...")
    with open("test_output.txt", "w") as f:
        f.write("Hello from multi-agent system!\n")
        f.write(f"Timestamp: {time.time()}\n")
    
    print("2. Reading test file...")
    with open("test_output.txt", "r") as f:
        content = f.read()
        print(f"Content: {content.strip()}")
    
    print("3. Checking if hooks captured these events...")
    print("   - PreToolUse should have logged Write and Read operations")
    print("   - PostToolUse should have logged successful completion")
    print("   - Events should appear in http://localhost:4000 dashboard")
    
    print("4. Cleaning up...")
    os.remove("test_output.txt")
    
    print("✅ Test completed! Check dashboard for events.")

if __name__ == "__main__":
    main()