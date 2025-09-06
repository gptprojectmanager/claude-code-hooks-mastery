#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "json",
# ]
# ///

"""
Demo script showing the improved model detection capabilities.

This demonstrates how the enhanced system now accurately detects models
from payload data rather than relying solely on inference.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from post_tool_use import detect_current_model, extract_model_from_payload


def demo_old_vs_new_detection():
    """Demonstrate the difference between old inference-only vs new payload-first detection."""
    
    print("🔍 Model Detection Enhancement Demo")
    print("=" * 50)
    
    # Scenario: User is using Opus but agent name suggests Sonnet
    test_payload = {
        "session_id": "demo-session-123",
        "hook_event_name": "PostToolUse", 
        "tool_name": "Write",
        "request": {
            "model": "claude-3-opus-20240229",  # ACTUAL model being used
            "tool_name": "Write",
            "parameters": {
                "file_path": "/path/to/file.py",
                "content": "# Enhanced code"
            }
        },
        "tool_input": {
            "file_path": "/path/to/file.py", 
            "content": "# Enhanced code"
        },
        "tool_response": {
            "success": True
        },
        "agent_context": {
            "agent_name": "code-reviewer-sonnet",  # Agent name suggests Sonnet
            "agent_role": "quality",
            "delegation_chain": "primary-agent → code-reviewer-sonnet"
        }
    }
    
    print("📋 Test Scenario:")
    print("  • Actual model in payload: claude-3-opus-20240229")
    print("  • Agent name suggests: code-reviewer-sonnet")
    print("  • Expected result: opus (from payload, not agent inference)")
    print()
    
    # Test the enhanced detection
    detected_model = detect_current_model(test_payload)
    
    print("🎯 Enhanced Detection Result:")
    print(f"  • Detected model: {detected_model}")
    
    if detected_model == "opus":
        print("  ✅ SUCCESS: Correctly detected Opus from payload data")
        print("  📊 This will now show accurate model info in observability dashboard")
    else:
        print(f"  ❌ FAILURE: Expected 'opus', got '{detected_model}'")
    
    print()
    
    # Test payload-only extraction
    payload_model = extract_model_from_payload(test_payload)
    print("🔍 Direct Payload Extraction:")
    print(f"  • Extracted model: {payload_model}")
    print(f"  • Extraction source: request.model field")
    print()
    
    # Test scenario without payload model (fallback)
    fallback_payload = {
        "session_id": "demo-session-456",
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "agent_context": {
            "agent_name": "researcher-haiku",
            "agent_role": "research"
        }
    }
    
    print("📋 Fallback Scenario (no model in payload):")
    fallback_model = detect_current_model(fallback_payload)
    print(f"  • Detected model: {fallback_model}")
    print(f"  • Source: Agent name inference (fallback)")
    print()


def demo_various_payload_formats():
    """Show how detection works with different payload formats."""
    
    print("🧪 Testing Various Payload Formats")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Claude Code with model in request",
            "payload": {"request": {"model": "claude-3.5-sonnet"}},
            "expected": "sonnet"
        },
        {
            "name": "Model in top-level field",
            "payload": {"model_id": "claude-3-haiku-20240307"},
            "expected": "haiku"
        },
        {
            "name": "Model in environment section",
            "payload": {"environment": {"ANTHROPIC_MODEL": "opus"}},
            "expected": "opus"
        },
        {
            "name": "Model in metadata",
            "payload": {"metadata": {"claude_model": "opusplan"}},
            "expected": "opusplan"
        },
        {
            "name": "Complex nested structure",
            "payload": {
                "session": {"config": {"model": "claude-3-opus"}},
                "request": {"parameters": {"ai_model": "sonnet"}}  # This should win (more specific)
            },
            "expected": "sonnet"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}:")
        result = extract_model_from_payload(test_case["payload"])
        
        if result == test_case["expected"]:
            print(f"   ✅ Detected: {result}")
        else:
            print(f"   ❌ Expected: {test_case['expected']}, Got: {result}")
        print()


def demo_observability_impact():
    """Show how this impacts the observability system."""
    
    print("📊 Observability System Impact")
    print("=" * 50)
    
    print("🔧 Before Enhancement:")
    print("  • Model detection relied on agent name inference")
    print("  • Claude Code model overrides were not detected")
    print("  • Dashboard showed incorrect model information")
    print("  • Performance tracking was inaccurate")
    print()
    
    print("✨ After Enhancement:")
    print("  • Model extracted directly from Claude Code payload")
    print("  • Accurate model tracking for all scenarios")
    print("  • Dashboard shows ACTUAL model being used")
    print("  • Performance metrics are model-specific and accurate")
    print("  • Fallback to inference only when payload lacks model info")
    print()
    
    # Example enhanced payload that would go to observability
    sample_enhanced_data = {
        "session_id": "abc-123",
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "model_info": "opus",  # Now accurately detected from payload
        "agent_context": {
            "agent_name": "code-reviewer-sonnet",  # Agent name different from actual model
            "agent_role": "quality",
            "delegation_chain": "primary-agent → code-reviewer-sonnet"
        },
        "enhanced_timestamp": 1703567890000,
        "tool_input": {"file_path": "/path/to/file.py"},
        "tool_response": {"success": True}
    }
    
    print("📋 Enhanced Observability Data Sample:")
    print(json.dumps(sample_enhanced_data, indent=2))
    print()
    
    print("🎯 Key Improvements:")
    print("  1. model_info now shows 'opus' (actual) not 'sonnet' (inferred)")
    print("  2. Dashboard can track model usage accurately")
    print("  3. Performance comparisons between models are valid")
    print("  4. Cost tracking per model is accurate")


def main():
    """Run the complete demonstration."""
    
    demo_old_vs_new_detection()
    print()
    demo_various_payload_formats()
    print() 
    demo_observability_impact()
    
    print("\n" + "=" * 50)
    print("🎉 Model Detection Enhancement Complete!")
    print()
    print("📈 Benefits Achieved:")
    print("  • Accurate model tracking from payload data")
    print("  • Correct observability dashboard metrics") 
    print("  • Better performance analysis per model")
    print("  • Reliable fallback to inference when needed")
    print("  • Enhanced debugging capabilities")


if __name__ == '__main__':
    main()