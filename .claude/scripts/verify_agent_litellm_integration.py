#!/usr/bin/env python3
"""
Verify Agent System liteLLM Integration
Simple verification script for Smart API Router integration
"""

import sys
import requests
import json
from pathlib import Path

def test_litellm_proxy():
    """Test liteLLM proxy accessibility"""
    print("🔌 Testing liteLLM Proxy Connection")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:4001/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            model_ids = [m.get('id') for m in models.get('data', [])]
            print(f"✅ liteLLM proxy accessible")
            print(f"✅ Available models: {model_ids}")
            return True
        else:
            print(f"❌ liteLLM proxy returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ liteLLM proxy not accessible: {e}")
        return False

def test_smart_api_router_import():
    """Test Smart API Router import"""
    print("\n🧭 Testing Smart API Router Import")
    print("-" * 40)
    
    try:
        sys.path.append('.claude/hooks')
        from utils.smart_api_router import SmartAPIRouter, create_smart_router
        print("✅ Smart API Router import successful")
        
        # Test instantiation
        router = create_smart_router()
        print("✅ Smart API Router instantiation successful")
        return True
    except ImportError as e:
        print(f"❌ Smart API Router import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Smart API Router instantiation failed: {e}")
        return False

def verify_agent_configurations():
    """Verify agent configurations have been updated"""
    print("\n📝 Verifying Agent Configuration Updates")
    print("-" * 40)
    
    configurations = {
        "Cipher MCP": ".claude/cipher-gemini.yml",
        "Safe liteLLM Wrapper": ".claude/scripts/safe-litellm-wrapper.py",
        "Safe liteLLM Commands": ".claude/commands/safe-litellm-analysis.md",
        "Code Reviewer liteLLM": ".claude/commands/agent_prompts/code_reviewer_litellm_prompt.md",
        "JavaScript Pro": ".claude/commands/agent_prompts/javascript_pro_prompt.md",
        "Python Pro": ".claude/commands/agent_prompts/python_pro_prompt.md"
    }
    
    success_count = 0
    total_count = len(configurations)
    
    for name, file_path in configurations.items():
        if Path(file_path).exists():
            print(f"✅ {name}: {file_path}")
            success_count += 1
        else:
            print(f"❌ {name}: {file_path} (missing)")
    
    print(f"\n📊 Configuration Files: {success_count}/{total_count} present")
    return success_count == total_count

def verify_litellm_routing_changes():
    """Verify key routing changes have been made"""
    print("\n🔄 Verifying liteLLM Routing Changes")
    print("-" * 40)
    
    checks = []
    
    # Check cipher configuration
    try:
        with open(".claude/cipher-gemini.yml", 'r') as f:
            cipher_content = f.read()
        
        has_proxy_endpoint = "localhost:4001" in cipher_content
        has_openai_provider = "provider: openai" in cipher_content
        
        if has_proxy_endpoint and has_openai_provider:
            print("✅ Cipher configured for liteLLM proxy routing")
            checks.append(True)
        else:
            print("❌ Cipher configuration incomplete")
            checks.append(False)
    except Exception as e:
        print(f"❌ Error checking cipher config: {e}")
        checks.append(False)
    
    # Check safe wrapper exists
    wrapper_exists = Path(".claude/scripts/safe-litellm-wrapper.py").exists()
    if wrapper_exists:
        print("✅ Safe liteLLM wrapper script created")
        checks.append(True)
    else:
        print("❌ Safe liteLLM wrapper script missing")
        checks.append(False)
    
    # Check agent prompts updated
    prompt_files = [
        ".claude/commands/agent_prompts/javascript_pro_prompt.md",
        ".claude/commands/agent_prompts/python_pro_prompt.md"
    ]
    
    prompt_checks = []
    for prompt_file in prompt_files:
        try:
            with open(prompt_file, 'r') as f:
                content = f.read()
            
            has_litellm_wrapper = "safe-litellm-wrapper.py" in content
            has_smart_router = "Smart API Router" in content
            
            if has_litellm_wrapper and has_smart_router:
                prompt_checks.append(True)
            else:
                prompt_checks.append(False)
        except Exception:
            prompt_checks.append(False)
    
    if all(prompt_checks):
        print("✅ Agent prompts updated for Smart API Router")
        checks.append(True)
    else:
        print("❌ Some agent prompts not fully updated")
        checks.append(False)
    
    return all(checks)

def main():
    """Run verification tests"""
    print("🔍 Agent System liteLLM Integration Verification")
    print("=" * 60)
    
    tests = [
        test_litellm_proxy(),
        test_smart_api_router_import(),
        verify_agent_configurations(),
        verify_litellm_routing_changes()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 Verification Summary")
    print("=" * 30)
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 SUCCESS: Agent system configured for liteLLM routing!")
        print("\n📋 Next Steps:")
        print("1. Test agent workflows with Smart API Router")
        print("2. Monitor routing decisions and fallback behavior")
        print("3. Verify Claude/Gemini routing works as expected")
        print("4. Update remaining agent prompts as needed")
        return True
    else:
        print(f"\n⚠️ INCOMPLETE: {total - passed} verification(s) failed")
        print("Review the output above and complete missing configurations")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)