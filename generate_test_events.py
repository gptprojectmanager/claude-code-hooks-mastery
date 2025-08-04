#!/usr/bin/env python3
"""
Generate test events for multi-agent observability dashboard
"""

import requests
import json
import time
import random
from datetime import datetime

# Server endpoint
SERVER_URL = "http://localhost:4000"

def send_event(event_data):
    """Send event to observability server"""
    try:
        response = requests.post(f"{SERVER_URL}/events", json=event_data)
        print(f"✅ Sent event: {event_data['type']} - Response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending event: {e}")
        return False

def generate_test_events():
    """Generate various test events"""
    
    agents = ["primary-agent", "code-reviewer", "planner", "coder", "tester"]
    tools = ["Write", "Read", "Bash", "Edit", "MultiEdit"]
    
    events = []
    
    # Generate some PreToolUse events
    for i in range(10):
        agent = random.choice(agents)
        tool = random.choice(tools)
        
        event = {
            "type": "PreToolUse",
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent,
            "data": {
                "tool_name": tool,
                "tool_input": f"Test input for {tool} #{i}",
                "session_id": f"session_{random.randint(1000, 9999)}"
            }
        }
        events.append(event)
        
        # Add corresponding PostToolUse event
        time.sleep(0.1)
        post_event = {
            "type": "PostToolUse",
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent,
            "data": {
                "tool_name": tool,
                "success": random.choice([True, True, True, False]),  # Mostly successful
                "duration_ms": random.randint(100, 2000),
                "session_id": f"session_{random.randint(1000, 9999)}"
            }
        }
        events.append(post_event)
    
    # Generate SubagentStop events
    for i in range(5):
        agent = random.choice(agents)
        event = {
            "type": "SubagentStop",
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent,
            "data": {
                "reason": random.choice(["task_completed", "user_interrupt", "error"]),
                "session_id": f"session_{random.randint(1000, 9999)}"
            }
        }
        events.append(event)
    
    return events

def main():
    print("🧪 Generating Test Events for Multi-Agent Observability Dashboard")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{SERVER_URL}/")
        print(f"✅ Server is running: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Generate and send events
    events = generate_test_events()
    
    print(f"\n📤 Sending {len(events)} test events...")
    
    successful = 0
    for event in events:
        if send_event(event):
            successful += 1
        time.sleep(0.2)  # Small delay between events
    
    print(f"\n📊 Results: {successful}/{len(events)} events sent successfully")
    print(f"🌐 Check dashboard at: http://localhost:4000")
    print(f"🔍 API test: curl http://localhost:4000/api/events/recent")

if __name__ == "__main__":
    main()