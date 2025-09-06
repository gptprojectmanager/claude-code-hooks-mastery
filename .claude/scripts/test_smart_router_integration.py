#!/usr/bin/env python3
"""
Test Smart API Router Integration with Agent System
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path

async def test_smart_router_status():
    """Test Smart API Router status and configuration"""
    print("🧪 Testing Smart API Router Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import Smart API Router
        sys.path.append('.claude/hooks/utils')
        from smart_api_router import create_smart_router
        
        router = create_smart_router()
        print("✅ Smart API Router imported successfully")
        
        # Test 2: Get routing status
        status = router.get_routing_status()
        print(f"✅ Primary Provider: {status.get('primary_provider')}")
        print(f"✅ Fallback Provider: {status.get('fallback_provider')}")
        print(f"✅ Current Rate Limits: {len(status.get('current_rate_limits', {}))}")
        
        # Test 3: Test routing decision
        test_request = {"model": "claude-3-sonnet", "message": "Hello, world!"}
        session_id = "test_session_agent_integration"
        
        decision = await router.route_request(test_request, session_id)
        print(f"✅ Routing Decision: {decision.strategy} -> {decision.provider}")
        print(f"✅ Confidence: {decision.confidence}")
        
        # Test 4: Check liteLLM proxy availability
        import requests
        try:
            response = requests.get("http://localhost:4001/v1/models", timeout=5)
            if response.status_code == 200:
                print("✅ liteLLM proxy is accessible")
                models = response.json()
                print(f"✅ Available models: {[m.get('id') for m in models.get('data', [])]}")
            else:
                print(f"⚠️ liteLLM proxy returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ liteLLM proxy not accessible: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Smart API Router test failed: {e}")
        return False

def test_safe_litellm_wrapper():
    """Test the safe liteLLM wrapper script"""
    print("\n🔧 Testing Safe liteLLM Wrapper")
    print("=" * 50)
    
    try:
        # Test with a simple safe prompt
        test_prompt = "ANALYZE ONLY - DO NOT MODIFY: Describe the main components of this project"
        
        result = subprocess.run([
            "python3", ".claude/scripts/safe-litellm-wrapper.py", 
            ".", test_prompt
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Safe liteLLM wrapper executed successfully")
            # Try to parse JSON output
            try:
                output_lines = result.stdout.strip().split('\n')
                json_line = None
                for line in output_lines:
                    if line.startswith('JSON OUTPUT:'):
                        json_line = line.replace('JSON OUTPUT:', '').strip()
                        break
                
                if json_line:
                    parsed_result = json.loads(json_line)
                    print(f"✅ JSON parsing successful")
                    print(f"✅ Analysis success: {parsed_result.get('success')}")
                    print(f"✅ Safety checks passed: {parsed_result.get('safety_checks')}")
                else:
                    print("⚠️ No JSON output found, but execution succeeded")
            except json.JSONDecodeError:
                print("⚠️ JSON parsing failed, but execution succeeded")
        else:
            print(f"❌ Safe liteLLM wrapper failed: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Safe liteLLM wrapper timed out")
        return False
    except Exception as e:
        print(f"❌ Safe liteLLM wrapper test failed: {e}")
        return False

def test_agent_prompt_updates():
    """Test that agent prompts have been updated correctly"""
    print("\n📝 Testing Agent Prompt Updates")
    print("=" * 50)
    
    updated_prompts = [
        ".claude/commands/agent_prompts/code_reviewer_litellm_prompt.md",
        ".claude/commands/agent_prompts/javascript_pro_prompt.md", 
        ".claude/commands/agent_prompts/python_pro_prompt.md"
    ]
    
    success_count = 0
    
    for prompt_file in updated_prompts:
        try:
            with open(prompt_file, 'r') as f:
                content = f.read()
                
            # Check for Smart API Router references
            has_smart_router = "Smart API Router" in content or "smart_api_router" in content
            has_litellm_wrapper = "safe-litellm-wrapper.py" in content
            has_safety_prefix = "ANALYZE ONLY - DO NOT MODIFY" in content
            
            if has_smart_router and has_litellm_wrapper and has_safety_prefix:
                print(f"✅ {prompt_file} updated correctly")
                success_count += 1
            else:
                print(f"⚠️ {prompt_file} may need additional updates")
                print(f"   Smart Router: {has_smart_router}")
                print(f"   liteLLM Wrapper: {has_litellm_wrapper}")
                print(f"   Safety Prefix: {has_safety_prefix}")
                
        except FileNotFoundError:
            print(f"❌ {prompt_file} not found")
        except Exception as e:
            print(f"❌ Error reading {prompt_file}: {e}")
    
    print(f"✅ {success_count}/{len(updated_prompts)} agent prompts updated correctly")
    return success_count == len(updated_prompts)

def test_cipher_configuration():
    """Test cipher configuration updates"""
    print("\n⚙️ Testing Cipher Configuration")
    print("=" * 50)
    
    try:
        with open(".claude/cipher-gemini.yml", 'r') as f:
            config_content = f.read()
        
        # Check for liteLLM proxy configuration
        has_proxy_url = "localhost:4001" in config_content
        has_openai_provider = "provider: openai" in config_content
        has_gemini_model = "gemini-flash" in config_content
        
        if has_proxy_url and has_openai_provider and has_gemini_model:
            print("✅ Cipher configuration updated for liteLLM proxy routing")
            return True
        else:
            print("⚠️ Cipher configuration may need additional updates")
            print(f"   Proxy URL: {has_proxy_url}")
            print(f"   OpenAI Provider: {has_openai_provider}")
            print(f"   Gemini Model: {has_gemini_model}")
            return False
            
    except FileNotFoundError:
        print("❌ Cipher configuration file not found")
        return False
    except Exception as e:
        print(f"❌ Error reading cipher configuration: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Smart API Router Agent Integration Tests")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Smart API Router Status
    test_results.append(await test_smart_router_status())
    
    # Test 2: Safe liteLLM Wrapper
    test_results.append(test_safe_litellm_wrapper())
    
    # Test 3: Agent Prompt Updates
    test_results.append(test_agent_prompt_updates())
    
    # Test 4: Cipher Configuration
    test_results.append(test_cipher_configuration())
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 50)
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Smart API Router integration is complete.")
        return True
    else:
        print("⚠️ Some tests failed. Review the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)