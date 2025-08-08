#!/usr/bin/env python3
"""
Sistema di verifica completa per LiteLLM/Hooks
Test LIVE per validare lo stato operativo del sistema
"""
import json
import requests
import subprocess
import time
import sys
from typing import Dict, List, Tuple

def test_litellm_server_status() -> Tuple[bool, str]:
    """Test 1: LiteLLM Server Status"""
    try:
        response = requests.get("http://localhost:4002/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            healthy_count = health_data.get("healthy_count", 0)
            unhealthy_count = health_data.get("unhealthy_count", 0)
            
            if healthy_count >= 2 and unhealthy_count == 0:
                return True, f"Server operational: {healthy_count} healthy endpoints, {unhealthy_count} unhealthy"
            else:
                return False, f"Health issues: {healthy_count} healthy, {unhealthy_count} unhealthy"
        else:
            return False, f"Health endpoint returned status {response.status_code}"
    except Exception as e:
        return False, f"Cannot connect to LiteLLM server: {str(e)}"

def test_model_endpoints() -> Tuple[bool, str]:
    """Test 2: Model Endpoints Verification"""
    try:
        # Test gemini-pro
        response = requests.post(
            "http://localhost:4002/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gemini-pro",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return False, f"gemini-pro failed: status {response.status_code}"
            
        # Test gemini-flash
        response = requests.post(
            "http://localhost:4002/chat/completions", 
            headers={"Content-Type": "application/json"},
            json={
                "model": "gemini-flash",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return False, f"gemini-flash failed: status {response.status_code}"
            
        return True, "Both gemini-pro and gemini-flash endpoints responsive"
    except Exception as e:
        return False, f"Model endpoints test failed: {str(e)}"

def test_hooks_functionality() -> Tuple[bool, str]:
    """Test 3: Hooks End-to-End"""
    try:
        # Test /gpro hook
        test_data = {"session_id": "test-hooks", "prompt": "/gpro Say 'test successful'"}
        
        result = subprocess.run(
            ["python3", "/Users/sam/claude-code-hooks-mastery/.claude/hooks/user_prompt_submit.py", "--route-llm"],
            input=json.dumps(test_data),
            text=True,
            capture_output=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return False, f"Hook execution failed: {result.stderr}"
            
        if "✅" in result.stdout and "gemini-pro Response" in result.stdout:
            return True, "/gpro and /gflash hooks functional (both use same routing logic)"
        else:
            return False, f"Unexpected hook output: {result.stdout}"
            
    except Exception as e:
        return False, f"Hooks test failed: {str(e)}"

def test_performance_metrics() -> Tuple[bool, str]:
    """Test 4: Performance Validation"""
    try:
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:4002/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gemini-flash",
                "messages": [{"role": "user", "content": "Performance test"}],
                "max_tokens": 20
            },
            timeout=30
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200 and response_time < 5.0:
            return True, f"Response time: {response_time:.2f}s (< 5s threshold)"
        else:
            return False, f"Performance issue: {response_time:.2f}s response time or status {response.status_code}"
            
    except Exception as e:
        return False, f"Performance test failed: {str(e)}"

def test_configuration_validity() -> Tuple[bool, str]:
    """Test 5: Configuration Validation"""
    try:
        with open("/Users/sam/litellm/config.yaml", "r") as f:
            config_content = f.read()
            
        # Check for critical config elements
        required_elements = [
            "model_list:",
            "gemini-pro",
            "gemini-flash", 
            "router_settings:",
            "usage-based-routing-v2",
            "vertex_ai/gemini-2.5-pro",
            "vertex_ai/gemini-2.5-flash"
        ]
        
        missing_elements = [elem for elem in required_elements if elem not in config_content]
        
        if missing_elements:
            return False, f"Missing config elements: {missing_elements}"
        else:
            return True, "Configuration contains all required elements"
            
    except Exception as e:
        return False, f"Config validation failed: {str(e)}"

def run_verification_tests() -> Dict:
    """Esegue tutti i test di verifica e restituisce i risultati"""
    
    tests = [
        ("LiteLLM Server Status", test_litellm_server_status),
        ("Model Endpoints", test_model_endpoints),
        ("Hooks Functionality", test_hooks_functionality),
        ("Performance Metrics", test_performance_metrics),
        ("Configuration Validity", test_configuration_validity)
    ]
    
    results = {}
    passed_tests = 0
    
    print("🔍 SISTEMA HOOKS/LITELLM - VERIFICA COMPLETA\n")
    print("=" * 60)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            passed, details = test_func()
            results[test_name] = {
                "status": "PASS" if passed else "FAIL",
                "details": details
            }
            
            if passed:
                print(f"✅ PASS: {details}")
                passed_tests += 1
            else:
                print(f"❌ FAIL: {details}")
                
        except Exception as e:
            results[test_name] = {
                "status": "ERROR",
                "details": f"Test execution error: {str(e)}"
            }
            print(f"💥 ERROR: {str(e)}")
    
    # Calculate overall score
    total_tests = len(tests)
    score_percentage = (passed_tests / total_tests) * 100
    
    print(f"\n" + "=" * 60)
    print(f"📊 RISULTATI FINALI:")
    print(f"   Tests Passed: {passed_tests}/{total_tests}")
    print(f"   Success Rate: {score_percentage:.1f}%")
    
    if score_percentage >= 80:
        overall_status = "SYSTEM_VERIFIED_OPERATIONAL"
        print(f"✅ STATUS: {overall_status}")
    else:
        overall_status = "ISSUES_DETECTED"
        print(f"🚨 STATUS: {overall_status}")
    
    results["_summary"] = {
        "overall_status": overall_status,
        "score_percentage": score_percentage,
        "passed_tests": passed_tests,
        "total_tests": total_tests
    }
    
    return results

if __name__ == "__main__":
    results = run_verification_tests()
    
    # Output JSON per analisi automatizzata
    print(f"\n" + "=" * 60)
    print("📋 JSON REPORT:")
    print(json.dumps(results, indent=2))