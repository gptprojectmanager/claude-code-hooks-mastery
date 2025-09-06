#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "asyncio",
#     "websockets", 
#     "google-cloud-secret-manager",
#     "pyyaml",
#     "numpy",
#     "httpx",
#     "anthropic",
#     "google-generativeai",
#     "openai"
# ]
# ///

import json
import os
import sys
import asyncio
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from utils.constants import ensure_session_log_dir
from utils.agent_detector import get_current_agent_context, build_agent_metadata
from utils.rate_limit_parser import parse_and_store_rate_limit

# Import continuous operations manager
try:
    from utils.continuous_operation_manager import ContinuousOperationManager
    from utils.smart_api_router import SmartAPIRouter
    CONTINUOUS_OPS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Continuous operations not available: {e}", file=sys.stderr)
    CONTINUOUS_OPS_AVAILABLE = False

# Import new advanced validation system
try:
    from collective_intelligence_validator import CollectiveIntelligenceValidator, trigger_advanced_ensemble_validation
    from meta_learning_thresholds import get_adaptive_thresholds_for_context, record_validation_feedback
    from population_consensus import ConsensusMethod
    from validation_telemetry import record_validation_event, record_validation_discovery, get_validation_dashboard, cleanup_validation_telemetry
    ADVANCED_VALIDATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Advanced validation system not available: {e}", file=sys.stderr)
    ADVANCED_VALIDATION_AVAILABLE = False

# FASE 5: Import enhanced model detection system
try:
    from utils.enhanced_model_detection import enhance_model_detection_with_fallbacks, get_enhanced_model_info
    ENHANCED_MODEL_DETECTION_AVAILABLE = True
    print("✅ Enhanced model detection system loaded", file=sys.stderr)
except ImportError as e:
    print(f"⚠️ Enhanced model detection not available: {e}", file=sys.stderr)
    ENHANCED_MODEL_DETECTION_AVAILABLE = False


def detect_embedded_gemini_events(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    ENHANCED: Detect Gemini API events embedded in tool_response.stdout that are NOT proxy calls.
    
    This addresses the critical gap where direct Gemini API calls were being missed.
    
    Args:
        payload: The complete JSON payload from stdin
        
    Returns:
        Tuple[bool, Optional[Dict]]: (is_gemini_direct, gemini_info_dict)
    """
    
    tool_response = payload.get('tool_response', {})
    if not isinstance(tool_response, dict):
        return False, None
    
    stdout = tool_response.get('stdout', '')
    if not stdout or not isinstance(stdout, str):
        return False, None
    
    try:
        # Try to parse stdout as JSON to look for embedded Gemini events
        if stdout.strip().startswith('{') and stdout.strip().endswith('}'):
            embedded_data = json.loads(stdout.strip())
            
            # Check for direct Gemini API patterns
            if isinstance(embedded_data, dict):
                # Pattern 1: Direct API response with model info
                model = embedded_data.get('model', '')
                api_type = embedded_data.get('api_type', '')
                proxy_type = embedded_data.get('proxy_type', '')
                
                if 'gemini' in model.lower() and proxy_type in ['none', None] and 'direct' in api_type:
                    return True, {
                        "event_type": "direct_gemini_api",
                        "api_type": "direct_gemini",
                        "provider": embedded_data.get('provider', 'google_ai_studio'),
                        "model": model,
                        "model_version": embedded_data.get('model_version', ''),
                        "proxy_type": "none",
                        "source": "tool_response_embedded"
                    }
                
                # Pattern 2: Gemini response with usage stats
                response_data = embedded_data.get('response', {})
                if isinstance(response_data, dict) and 'gemini' in response_data.get('model', '').lower():
                    return True, {
                        "event_type": "direct_gemini_api",
                        "api_type": "direct_gemini", 
                        "provider": "google_ai_studio",
                        "model": response_data.get('model', 'gemini-2.5-pro'),
                        "model_version": "2.5-pro" if '2.5' in response_data.get('model', '') else 'unknown',
                        "proxy_type": "none",
                        "source": "tool_response_embedded"
                    }
        
        # Pattern 3: Look for Gemini model names in stdout text
        gemini_model_patterns = [
            r'gemini-2\.5-pro',
            r'gemini-2\.5-flash',
            r'gemini-pro',
            r'gemini-flash'
        ]
        
        for pattern in gemini_model_patterns:
            matches = re.findall(pattern, stdout, re.IGNORECASE)
            if matches and 'proxy' not in stdout.lower() and 'litellm' not in stdout.lower():
                # Found direct Gemini reference, not proxy
                return True, {
                    "event_type": "direct_gemini_reference",
                    "api_type": "direct_gemini",
                    "provider": "google_ai_studio", 
                    "model": matches[0],
                    "model_version": matches[0].replace('gemini-', '') if matches[0].startswith('gemini-') else 'unknown',
                    "proxy_type": "none",
                    "source": "tool_response_text"
                }
                
    except (json.JSONDecodeError, ValueError):
        # stdout is not JSON, continue with text pattern matching
        pass
    except Exception as e:
        print(f"⚠️ Error parsing embedded Gemini events: {e}", file=sys.stderr)
    
    return False, None


def detect_litellm_proxy_usage(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    ENHANCED: Detect if the request is using liteLLM proxy and extract proxy information.
    
    Now includes better detection for various proxy patterns and distinguishes from direct API.
    
    Args:
        payload: The complete JSON payload from stdin
        
    Returns:
        Tuple[bool, Optional[Dict]]: (is_using_proxy, proxy_info_dict)
    """
    
    proxy_indicators = [
        'localhost:4001',
        'litellm',
        '127.0.0.1:4001',
        'http://localhost:4001',
        'https://localhost:4001',
        'litellm-proxy',
        'proxy_gemini'
    ]
    
    # Check for proxy indicators in various payload fields
    payload_str = json.dumps(payload).lower()
    
    for indicator in proxy_indicators:
        if indicator in payload_str:
            return True, {
                "proxy_type": "litellm",
                "proxy_url": "http://localhost:4001",
                "api_type": "proxy_gemini",
                "event_type": "litellm_proxy_request"
            }
    
    # Check tool_response.stdout for liteLLM monitor data
    tool_response = payload.get('tool_response', {})
    if isinstance(tool_response, dict):
        stdout = tool_response.get('stdout', '')
        if stdout and isinstance(stdout, str):
            # Look for explicit liteLLM monitor events in stdout
            if 'litellm-monitor' in stdout or 'proxy_type' in stdout and 'litellm' in stdout:
                # Try to extract model info from the stdout
                model_info = extract_model_from_litellm_stdout(stdout)
                if model_info:
                    return True, {
                        "proxy_type": "litellm",
                        "proxy_url": "http://localhost:4001",
                        "api_type": "proxy_gemini",
                        "extracted_model": model_info,
                        "event_type": "litellm_monitor_event"
                    }
                else:
                    return True, {
                        "proxy_type": "litellm",
                        "proxy_url": "http://localhost:4001", 
                        "api_type": "proxy_gemini",
                        "event_type": "litellm_monitor_event"
                    }
    
    return False, None


def classify_event_source(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    NEW: Unified event source classification that distinguishes between:
    - liteLLM proxy calls
    - Direct Gemini API calls  
    - Direct Anthropic API calls
    - Other API calls
    
    Args:
        payload: The complete JSON payload from stdin
        
    Returns:
        Dict with complete event source classification
    """
    
    # Priority 1: Check for liteLLM proxy usage
    is_proxy, proxy_info = detect_litellm_proxy_usage(payload)
    if is_proxy and proxy_info:
        return {
            "event_classification": "litellm_proxy",
            "api_type": "proxy_gemini",
            "provider": "gemini_via_proxy",
            "proxy_type": "litellm",
            "routing": "proxy",
            **proxy_info
        }
    
    # Priority 2: Check for embedded Gemini direct API calls
    is_direct_gemini, gemini_info = detect_embedded_gemini_events(payload)
    if is_direct_gemini and gemini_info:
        return {
            "event_classification": "direct_gemini_api",
            "api_type": "direct_gemini",
            "provider": "google_ai_studio",
            "proxy_type": "none",
            "routing": "direct",
            **gemini_info
        }
    
    # Priority 3: Check for Anthropic/Claude API usage (default case)
    model_info = extract_model_from_payload_claude_only(payload)
    if model_info:
        return {
            "event_classification": "direct_anthropic_api",
            "api_type": "direct_anthropic",
            "provider": "anthropic",
            "proxy_type": "none",  
            "routing": "direct",
            "model": model_info
        }
    
    # Fallback: Unknown classification
    return {
        "event_classification": "unknown",
        "api_type": "unknown", 
        "provider": "unknown",
        "proxy_type": "unknown",
        "routing": "unknown"
    }


def extract_model_from_payload_claude_only(payload: Dict[str, Any]) -> Optional[str]:
    """
    DETERMINISTIC: Extract Claude model ONLY from actual API response data.
    NO agent name inference - only real API data.
    """
    
    if not isinstance(payload, dict):
        return None
    
    # Priority 1: Check tool_response for actual API model info
    tool_response = payload.get('tool_response', {})
    if isinstance(tool_response, dict):
        # Check for model in API response headers or metadata
        api_metadata = tool_response.get('metadata', {})
        if isinstance(api_metadata, dict):
            model = api_metadata.get('model')
            if model and 'claude' in str(model).lower():
                return _extract_claude_model_from_string(str(model))
        
        # Check response content for model indicators
        response_model = tool_response.get('model')
        if response_model and 'claude' in str(response_model).lower():
            return _extract_claude_model_from_string(str(response_model))
    
    # Priority 2: Check request for actual API model specification
    request = payload.get('request', {})
    if isinstance(request, dict):
        # Check for model in API request parameters (real API calls)
        api_params = request.get('parameters', {})
        if isinstance(api_params, dict):
            model = api_params.get('model')
            if model and 'claude' in str(model).lower():
                return _extract_claude_model_from_string(str(model))
        
        # Check for model in request headers
        headers = request.get('headers', {})
        if isinstance(headers, dict):
            model = headers.get('x-anthropic-model') or headers.get('anthropic-model')
            if model:
                return _extract_claude_model_from_string(str(model))
    
    # Priority 3: Check for model in actual API response data
    response = payload.get('response', {})
    if isinstance(response, dict):
        # Look for model in response metadata
        if 'model' in response and 'claude' in str(response['model']).lower():
            return _extract_claude_model_from_string(str(response['model']))
    
    # NO FALLBACK to agent names - return None if no API data found
    return None


def _extract_claude_model_from_string(text: str) -> Optional[str]:
    """Extract Claude model name from a string value (excludes Gemini models)."""
    if not isinstance(text, str):
        return None
    
    text_lower = text.lower()
    
    # Skip if this contains Gemini references
    if 'gemini' in text_lower:
        return None
    
    # Check for Claude model patterns (order matters - check longer names first)
    model_patterns = [
        ('opusplan', ['opusplan', 'opus-plan', 'opus_plan']),
        ('opus', ['opus', 'claude-3-opus', 'claude-opus', 'sonnet-4']),  
        ('sonnet', ['sonnet', 'claude-3-sonnet', 'claude-sonnet', 'claude-3.5-sonnet', 'claude-sonnet-4']),
        ('haiku', ['haiku', 'claude-3-haiku', 'claude-haiku'])
    ]
    
    for model_name, patterns in model_patterns:
        for pattern in patterns:
            if pattern in text_lower:
                return model_name
    
    return None


def extract_model_from_litellm_stdout(stdout: str) -> Optional[str]:
    """
    Extract model information from liteLLM monitor output in tool_response.stdout.
    
    Args:
        stdout: The stdout content from tool response
        
    Returns:
        str: Extracted model information or None
    """
    
    try:
        # Look for model_info patterns in the stdout
        # Pattern: "model_info":"provider:gemini,version:2.5-pro,model:gemini-2.5-pro"
        model_patterns = [
            r'"model_info"\s*:\s*"([^"]*gemini[^"]*)"',
            r"'model_info'\s*:\s*'([^']*gemini[^']*)'",
            r'model_info["\']?\s*[:=]\s*["\']?([^"\',]*gemini[^"\',]*)["\']?'
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, stdout, re.IGNORECASE)
            if matches:
                model_info = matches[0]
                # Parse the structured model info
                if "provider:gemini" in model_info:
                    return model_info  # Return full info: "provider:gemini,version:2.5-pro,model:gemini-2.5-pro"
        
        # Look for simple gemini model references
        simple_patterns = [
            r'(gemini-2\.5-pro)',
            r'(gemini-2\.5-flash)',
            r'(gemini-pro)',
            r'(gemini-flash)'
        ]
        
        for pattern in simple_patterns:
            matches = re.findall(pattern, stdout, re.IGNORECASE)
            if matches:
                return f"model:gemini,version:{matches[0].replace('gemini-', '')}"
                
    except Exception as e:
        print(f"⚠️ Error parsing liteLLM stdout: {e}", file=sys.stderr)
    
    return None


def extract_model_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    DETERMINISTIC: Extract model information ONLY from actual API calls.
    NO inference from agent names - completely deterministic.
    
    Priority order:
    1. liteLLM proxy detection (actual proxy call)
    2. Direct Gemini API detection (actual Gemini API)
    3. Claude model detection (actual Claude API)
    4. Return "unknown" - NO FALLBACK INFERENCE
    """
    
    if not isinstance(payload, dict):
        return "unknown"
    
    # Get unified event classification
    event_source = classify_event_source(payload)
    
    if event_source["event_classification"] == "litellm_proxy":
        # Extract proxy model info from actual proxy response
        extracted_model = event_source.get('extracted_model')
        if extracted_model:
            return extracted_model
        else:
            # If proxy detected but no model info, still indicate it's via proxy
            return "provider:gemini,version:2.5-pro,model:gemini-2.5-pro,proxy:litellm"
    
    elif event_source["event_classification"] == "direct_gemini_api":
        # Extract direct Gemini model info from actual API response
        model = event_source.get('model', 'gemini-2.5-pro')
        version = event_source.get('model_version', '2.5-pro')
        return f"provider:gemini,version:{version},model:{model},api:direct"
    
    elif event_source["event_classification"] == "direct_anthropic_api":
        # Extract Claude model info from actual API response
        model = event_source.get('model')
        if model:
            return model
        else:
            # Even for Claude, if no model in actual API data, return unknown
            return "unknown"
    
    # NO FALLBACK - return unknown if no actual API data found
    return "unknown"


def detect_current_model(payload: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    FASE 5 ENHANCED: Model detection with intelligent fallbacks.
    
    This function now uses the enhanced detection system which provides
    intelligent fallbacks while maintaining deterministic priority.
    
    Args:
        payload: JSON payload from stdin containing actual API call/response data
    
    Returns:
        - Actual model info from API calls (Priority 1)
        - Intelligent fallback detection (Priority 2-4)
        - NEVER returns "unknown" anymore
    """
    
    if payload is None:
        print("⚠️ No payload provided for model detection", file=sys.stderr)
        return "provider:claude,model:sonnet,source:no_payload,confidence:low"
    
    # FASE 5: Use enhanced model detection with fallbacks
    if ENHANCED_MODEL_DETECTION_AVAILABLE:
        try:
            enhanced_result = enhance_model_detection_with_fallbacks(payload)
            if enhanced_result:
                print(f"✅ Enhanced model detected: {enhanced_result}", file=sys.stderr)
                return enhanced_result
        except Exception as e:
            print(f"⚠️ Enhanced detection failed: {e}", file=sys.stderr)
    
    # Fallback to original deterministic detection
    model = extract_model_from_payload(payload)
    
    if model and model != "unknown":
        print(f"🎯 Deterministic model detected: {model}", file=sys.stderr)
        return model
    else:
        # Final fallback - provide intelligent default instead of "unknown"
        print("🔮 Using final fallback model detection", file=sys.stderr)
        return "provider:claude,model:sonnet,source:final_fallback,confidence:low"


def _search_payload_for_model_string(data: Any, model_name: str) -> bool:
    """Recursively search payload for model name strings."""
    if isinstance(data, dict):
        for key, value in data.items():
            # Check key names for model indicators
            if model_name.lower() in key.lower():
                return True
            # Recursively search values
            if _search_payload_for_model_string(value, model_name):
                return True
    elif isinstance(data, list):
        for item in data:
            if _search_payload_for_model_string(item, model_name):
                return True
    elif isinstance(data, str):
        if model_name.lower() in data.lower():
            return True
    
    return False


def extract_unified_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    FASE 5 ENHANCED: Extract comprehensive metadata using unified event classification.
    
    This replaces the old extract_proxy_metadata with complete event source analysis
    and now includes enhanced model detection metadata.
    
    Args:
        payload: The complete JSON payload from stdin
        
    Returns:
        Dict with unified event metadata
    """
    
    # Get unified event classification
    event_source = classify_event_source(payload)
    
    # Base metadata from classification
    metadata = {
        "event_classification": event_source["event_classification"],
        "api_type": event_source["api_type"],
        "provider": event_source["provider"],
        "proxy_type": event_source["proxy_type"],
        "routing": event_source["routing"]
    }
    
    # FASE 5: Add enhanced model detection metadata
    if ENHANCED_MODEL_DETECTION_AVAILABLE:
        try:
            enhanced_model_info = get_enhanced_model_info(payload)
            metadata.update({
                "enhanced_model_detection": enhanced_model_info.get("enhanced_detection", False),
                "detection_confidence": enhanced_model_info.get("confidence", "unknown"),
                "detection_source": enhanced_model_info.get("detection_source", "unknown"),
                "model_provider": enhanced_model_info.get("provider", "unknown"),
                "model_version": enhanced_model_info.get("model_version", ""),
                "detection_timestamp": enhanced_model_info.get("detection_timestamp")
            })
        except Exception as e:
            print(f"⚠️ Error adding enhanced model metadata: {e}", file=sys.stderr)
    
    # Add model-specific metadata based on classification
    if event_source["event_classification"] == "litellm_proxy":
        metadata.update({
            "model_type": "gemini",
            "model_version": "2.5-pro",  # Could extract from event_source
            "proxy_url": "http://localhost:4001",
            "event_source": "litellm_proxy"
        })
    elif event_source["event_classification"] == "direct_gemini_api":
        metadata.update({
            "model_type": "gemini",
            "model_version": event_source.get("model_version", "2.5-pro"),
            "event_source": event_source.get("source", "direct_api"),
            "model": event_source.get("model", "gemini-2.5-pro")
        })
    elif event_source["event_classification"] == "direct_anthropic_api":
        metadata.update({
            "model_type": "claude",
            "model_version": event_source.get("model", "sonnet"),
            "event_source": "direct_api"
        })
    
    return metadata


def is_task_completion_event(input_data: Dict[str, Any]) -> bool:
    """
    Detect if this tool use represents a task completion event.
    
    Task completion indicators:
    - mcp__shrimp-task-manager__verify_task calls
    - Tools with high success scores (≥80)
    - Primary agent orchestration completion patterns
    - Work validator successful completions
    """
    
    tool_name = input_data.get('request', {}).get('tool_name', '')
    tool_params = input_data.get('request', {}).get('parameters', {})
    
    # Direct task completion via Shrimp Task Manager
    if 'shrimp-task-manager' in tool_name and 'verify' in tool_name:
        score = tool_params.get('score', 0)
        return score >= 80
    
    # Work validator completion patterns
    if 'work-validator' in tool_name or input_data.get('agent_name') == 'work-validator-sonnet':
        # Check for validation completion in response
        response_content = str(input_data.get('response', {}))
        if 'validation_status' in response_content and 'approved' in response_content:
            return True
    
    # Primary agent completion patterns
    agent_context = get_current_agent_context()
    if agent_context.get('agent_name') == 'primary-agent':
        # Check for completion indicators in tool usage patterns
        completion_patterns = ['completed', 'finished', 'done', 'success']
        response_str = str(input_data.get('response', '')).lower()
        
        if any(pattern in response_str for pattern in completion_patterns):
            return True
    
    return False


def is_primary_agent_active() -> bool:
    """Check if Primary Agent is currently active using agent_detector patterns."""
    agent_context = get_current_agent_context()
    return agent_context.get('agent_name') == 'primary-agent'


def enhance_with_workflow_context(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance event data with workflow context for Shrimp and Cipher tool events.
    Non-breaking enhancement that adds workflow_context and memory_context fields.
    
    Args:
        input_data: Original tool event data
        
    Returns:
        Enhanced data with workflow context information
    """
    
    enhanced_data = input_data.copy()
    tool_name = input_data.get('request', {}).get('tool_name', '')
    
    # Detect Shrimp tool events
    if 'shrimp' in tool_name.lower() or 'mcp__shrimp-task-manager' in tool_name:
        workflow_context = _get_shrimp_workflow_context(input_data)
        if workflow_context:
            enhanced_data['workflow_context'] = workflow_context
    
    # Detect Cipher operations
    if 'cipher' in tool_name.lower() or _detect_cipher_operation(input_data):
        memory_context = _get_cipher_memory_context(input_data)
        if memory_context:
            enhanced_data['memory_context'] = memory_context
    
    return enhanced_data


def _get_shrimp_workflow_context(input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract workflow context from Shrimp task manager events."""
    try:
        tool_params = input_data.get('request', {}).get('parameters', {})
        task_id = tool_params.get('taskId') or tool_params.get('task_id')
        
        if not task_id:
            # Try to extract task ID from response
            response = input_data.get('response', {})
            if isinstance(response, dict):
                task_id = response.get('taskId') or response.get('task_id')
        
        if task_id:
            # Attempt to fetch task data from Shrimp API
            try:
                import httpx
                import asyncio
                
                async def fetch_task_data():
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        response = await client.get(f"http://localhost:62369/api/tasks/{task_id}")
                        if response.status_code == 200:
                            return response.json()
                    return None
                
                # Run async fetch in sync context
                try:
                    loop = asyncio.get_event_loop()
                    task_data = loop.run_until_complete(fetch_task_data())
                except RuntimeError:
                    # No event loop running, create new one
                    task_data = asyncio.run(fetch_task_data())
                
                if task_data:
                    return {
                        'task_id': task_id,
                        'task_name': task_data.get('name', 'Unknown Task'),
                        'dependencies': task_data.get('dependencies', []),
                        'workflow_stage': task_data.get('status', 'unknown'),
                        'completion_percentage': _calculate_task_completion(task_data),
                        'related_tasks': task_data.get('relatedTasks', []),
                        'workflow_type': 'shrimp_task_management'
                    }
                    
            except Exception as e:
                print(f"⚠️ Error fetching Shrimp task data: {e}", file=sys.stderr)
        
        # Fallback context from available data
        return {
            'task_id': task_id or 'unknown',
            'task_name': tool_params.get('name', 'Unknown Task'),
            'workflow_stage': tool_params.get('status', 'in_progress'),
            'workflow_type': 'shrimp_task_management',
            'context_source': 'fallback_params'
        }
        
    except Exception as e:
        print(f"⚠️ Error creating workflow context: {e}", file=sys.stderr)
        return None


def _get_cipher_memory_context(input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract memory context from Cipher operations."""
    try:
        tool_name = input_data.get('request', {}).get('tool_name', '')
        tool_params = input_data.get('request', {}).get('parameters', {})
        response = input_data.get('response', {})
        
        memory_context = {
            'operation_type': _detect_cipher_operation_type(tool_name, tool_params),
            'memory_patterns_accessed': [],
            'knowledge_graph_updates': False,
            'context_enrichment': False,
            'memory_type': 'cipher_knowledge_graph'
        }
        
        # Detect memory pattern access
        if isinstance(response, dict):
            # Check for pattern references in response
            response_str = str(response).lower()
            if 'pattern' in response_str or 'memory' in response_str:
                memory_context['memory_patterns_accessed'] = _extract_pattern_references(response)
                memory_context['context_enrichment'] = True
        
        # Detect knowledge graph updates
        if 'store' in tool_name.lower() or 'add' in tool_name.lower():
            memory_context['knowledge_graph_updates'] = True
        
        # Add session context
        memory_context['session_context'] = {
            'session_id': input_data.get('session_id', 'unknown'),
            'agent_context': get_current_agent_context().get('agent_name', 'unknown')
        }
        
        return memory_context
        
    except Exception as e:
        print(f"⚠️ Error creating memory context: {e}", file=sys.stderr)
        return None


def _detect_cipher_operation(input_data: Dict[str, Any]) -> bool:
    """Detect if this is a Cipher memory operation."""
    tool_name = input_data.get('request', {}).get('tool_name', '')
    tool_params = input_data.get('request', {}).get('parameters', {})
    
    # Direct cipher tool usage
    if 'cipher' in tool_name.lower():
        return True
    
    # Cipher CLI operations in Bash tools
    if tool_name == 'Bash':
        command = tool_params.get('command', '')
        if 'cipher' in command:
            return True
    
    # Memory-related MCP tools that might use Cipher
    memory_tools = ['krag-graphiti-memory', 'memory', 'knowledge']
    return any(tool in tool_name.lower() for tool in memory_tools)


def _detect_cipher_operation_type(tool_name: str, tool_params: Dict[str, Any]) -> str:
    """Detect the type of Cipher operation being performed."""
    if 'search' in tool_name.lower() or 'query' in tool_name.lower():
        return 'memory_search'
    elif 'store' in tool_name.lower() or 'add' in tool_name.lower():
        return 'memory_storage'
    elif 'update' in tool_name.lower() or 'modify' in tool_name.lower():
        return 'memory_update'
    elif 'delete' in tool_name.lower() or 'remove' in tool_name.lower():
        return 'memory_deletion'
    else:
        return 'memory_access'


def _extract_pattern_references(response: Dict[str, Any]) -> List[str]:
    """Extract memory pattern references from response data."""
    patterns = []
    
    try:
        # Look for pattern arrays in response
        if 'patterns' in response and isinstance(response['patterns'], list):
            patterns.extend([str(p) for p in response['patterns'][:5]])  # Limit to 5
        
        # Look for memory references
        if 'memory_refs' in response and isinstance(response['memory_refs'], list):
            patterns.extend([str(ref) for ref in response['memory_refs'][:5]])
        
        # Look for pattern IDs or names in string responses
        response_str = str(response)
        import re
        pattern_matches = re.findall(r'pattern[_-]?(\w+)', response_str, re.IGNORECASE)
        patterns.extend(pattern_matches[:3])  # Limit pattern matches
        
    except Exception:
        pass
    
    return patterns


def _calculate_task_completion(task_data: Dict[str, Any]) -> float:
    """Calculate task completion percentage from task data."""
    try:
        status = task_data.get('status', '').lower()
        
        # Simple status-based completion mapping
        completion_map = {
            'completed': 100.0,
            'in_progress': 50.0,
            'pending': 0.0,
            'blocked': 25.0,
            'failed': 0.0
        }
        
        return completion_map.get(status, 25.0)  # Default to 25% if unknown
        
    except Exception:
        return 0.0


async def trigger_enhanced_memory_sync(input_data: Dict[str, Any]) -> bool:
    """
    Trigger enhanced memory sync using the new memory_sync_enhanced.py script.
    
    This calls the enhanced memory sync when significant task completions occur,
    ensuring context and knowledge are preserved across sessions.
    """
    
    try:
        # Import the enhanced memory sync module
        script_path = Path(__file__).parent / "utils" / "agentic_enhanced" / "memory_sync_enhanced.py"
        
        if not script_path.exists():
            return False
        
        # Extract relevant context for memory storage
        context_data = {
            "completion_event": input_data,
            "agent_context": get_current_agent_context(),
            "timestamp": int(time.time() * 1000),
            "tool_usage": {
                "tool_name": input_data.get('request', {}).get('tool_name'),
                "success": input_data.get('response', {}).get('success', False)
            }
        }
        
        # Create memory entry for the completion event
        import subprocess
        memory_content = f"Task completion: {context_data['tool_usage']['tool_name']} completed successfully"
        
        result = subprocess.run([
            str(script_path), "add", memory_content
        ], capture_output=True, text=True, timeout=30)
        
        return result.returncode == 0
        
    except Exception as e:
        # Log error but don't fail the hook
        print(f"Memory sync error: {e}", file=sys.stderr)
        return False


async def trigger_ensemble_validation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trigger advanced ensemble validation using the new collective intelligence system.
    
    This replaces the previous primitive validation with sophisticated multi-model
    validation using adaptive thresholds and collective intelligence patterns.
    """
    
    try:
        # Check if this is a validation-worthy event
        if not is_task_completion_event(input_data) and not is_primary_agent_active():
            return {"ensemble_validation": "not_applicable"}
        
        if ADVANCED_VALIDATION_AVAILABLE:
            # Use advanced collective intelligence validation
            print("🧠 Using advanced collective intelligence validation", file=sys.stderr)
            return await trigger_advanced_ensemble_validation(input_data)
        else:
            # Fallback to improved legacy validation
            return await _fallback_ensemble_validation(input_data)
        
    except Exception as e:
        return {
            "ensemble_validation": "error",
            "error": str(e),
            "fallback_available": True
        }


async def _fallback_ensemble_validation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Improved fallback validation when advanced system is not available.
    """
    validation_result = {
        "ensemble_validation": "fallback_legacy",
        "models_used": [],
        "consensus_score": 0,
        "validation_details": {}
    }
    
    try:
        # Model 1: Improved Opus validation with better heuristics
        opus_result = await run_opus_validation(input_data)
        validation_result["models_used"].append("opus")
        validation_result["validation_details"]["opus"] = opus_result
        
        # Model 2: Improved Gemini validation with better heuristics
        gemini_result = await run_gemini_validation(input_data)
        validation_result["models_used"].append("gemini_gpro")
        validation_result["validation_details"]["gemini"] = gemini_result
        
        # Calculate improved consensus using weighted scoring
        opus_weight = opus_result.get("confidence", 0.5) if "error" not in opus_result else 0.1
        gemini_weight = gemini_result.get("confidence", 0.5) if "error" not in gemini_result else 0.1
        
        total_weight = opus_weight + gemini_weight
        
        if total_weight > 0:
            validation_result["consensus_score"] = (
                (opus_result.get("score", 0) * opus_weight + 
                 gemini_result.get("score", 0) * gemini_weight) / total_weight
            )
        else:
            validation_result["consensus_score"] = 50.0  # Conservative default
        
        # Use adaptive thresholds if available
        if ADVANCED_VALIDATION_AVAILABLE:
            try:
                adaptive_thresholds = get_adaptive_thresholds_for_context(input_data)
                approved_threshold = adaptive_thresholds.get("approved", 80.0)
                needs_revision_threshold = adaptive_thresholds.get("needs_revision", 60.0)
            except:
                approved_threshold = 80.0
                needs_revision_threshold = 60.0
        else:
            approved_threshold = 80.0
            needs_revision_threshold = 60.0
        
        # Determine final validation status
        if validation_result["consensus_score"] >= approved_threshold:
            validation_result["final_status"] = "approved"
        elif validation_result["consensus_score"] >= needs_revision_threshold:
            validation_result["final_status"] = "needs_revision" 
        else:
            validation_result["final_status"] = "rejected"
        
        return validation_result
        
    except Exception as e:
        return {
            "ensemble_validation": "fallback_error",
            "error": str(e)
        }


async def run_opus_validation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced Opus model validation.
    
    If advanced system is available, uses real API calls.
    Otherwise provides improved heuristic-based validation.
    """
    
    if ADVANCED_VALIDATION_AVAILABLE:
        try:
            validator = CollectiveIntelligenceValidator()
            from collective_intelligence_validator import ValidationModel
            result = await validator._validate_with_model(ValidationModel.CLAUDE_OPUS, input_data)
            
            return {
                "model": "opus",
                "score": result.score,
                "reflection": result.reasoning,
                "recommendations": ["Consider ensemble validation", "Review safety scores"],
                "confidence": result.confidence,
                "tokens_used": result.tokens_used,
                "dimensions": result.dimensions.__dict__ if hasattr(result, 'dimensions') else {},
                "response_time": result.response_time
            }
        except Exception as e:
            print(f"Advanced Opus validation failed: {e}", file=sys.stderr)
            # Fall through to heuristic validation
    
    # Improved heuristic-based validation
    tool_name = input_data.get('request', {}).get('tool_name', '')
    tool_params = input_data.get('request', {}).get('parameters', {})
    response_content = input_data.get('response', {})
    
    # Heuristic scoring based on tool type and success indicators
    base_score = 70.0
    confidence = 0.6  # Lower confidence for heuristic
    
    # Tool-specific scoring
    tool_scores = {
        'Write': 80.0,
        'Read': 75.0,
        'Bash': 85.0,
        'git': 82.0,
        'search': 70.0
    }
    
    base_score = tool_scores.get(tool_name, base_score)
    
    # Success indicators
    if response_content.get('success', False):
        base_score += 10.0
        confidence += 0.1
    
    # Error indicators
    if 'error' in str(response_content).lower():
        base_score -= 15.0
        confidence -= 0.1
    
    # Parameter complexity (more complex = potentially higher quality if successful)
    param_complexity = len(str(tool_params)) / 100.0
    base_score += min(5.0, param_complexity)
    
    # Constrain score and confidence
    final_score = max(10.0, min(95.0, base_score))
    final_confidence = max(0.2, min(0.8, confidence))
    
    return {
        "model": "opus",
        "score": final_score,
        "reflection": f"Heuristic analysis of {tool_name} usage with complexity {param_complexity:.2f}",
        "recommendations": ["Consider using real API validation", "Review parameter complexity"],
        "confidence": final_confidence,
        "tokens_used": 0,  # No actual API call
        "dimensions": {
            "performance": final_score * 0.9,
            "novelty": final_score * 0.7,
            "efficiency": final_score * 0.8,
            "safety": final_score * 1.1
        }
    }


async def run_gemini_validation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced Gemini GPro validation.
    
    If advanced system is available, uses real API calls.
    Otherwise provides improved heuristic-based validation.
    """
    
    if ADVANCED_VALIDATION_AVAILABLE:
        try:
            validator = CollectiveIntelligenceValidator()
            from collective_intelligence_validator import ValidationModel
            result = await validator._validate_with_model(ValidationModel.GEMINI_PRO, input_data)
            
            return {
                "model": "gemini_gpro", 
                "score": result.score,
                "analysis": result.reasoning,
                "hook_context": "Validated through advanced API integration",
                "confidence": result.confidence,
                "tokens_used": result.tokens_used,
                "dimensions": result.dimensions.__dict__ if hasattr(result, 'dimensions') else {},
                "response_time": result.response_time
            }
        except Exception as e:
            print(f"Advanced Gemini validation failed: {e}", file=sys.stderr)
            # Fall through to heuristic validation
    
    # Improved heuristic-based validation (slightly different from Opus)
    tool_name = input_data.get('request', {}).get('tool_name', '')
    tool_params = input_data.get('request', {}).get('parameters', {})
    response_content = input_data.get('response', {})
    
    # Different base scoring for diversity
    base_score = 68.0
    confidence = 0.55
    
    # Different tool scoring to provide diversity
    tool_scores = {
        'Write': 78.0,
        'Read': 72.0,
        'Bash': 88.0,  # Gemini might be better at shell analysis
        'git': 80.0,
        'search': 74.0
    }
    
    base_score = tool_scores.get(tool_name, base_score)
    
    # Different success weighting
    if response_content.get('success', False):
        base_score += 12.0
        confidence += 0.15
    
    # Different error penalty
    if 'error' in str(response_content).lower():
        base_score -= 12.0
        confidence -= 0.05
    
    # Response size factor (Gemini might prefer detailed responses)
    response_size = len(str(response_content)) / 200.0
    base_score += min(3.0, response_size)
    
    # Constrain values
    final_score = max(15.0, min(92.0, base_score))
    final_confidence = max(0.25, min(0.85, confidence))
    
    return {
        "model": "gemini_gpro",
        "score": final_score,
        "analysis": f"Heuristic analysis of {tool_name} with response complexity {response_size:.2f}",
        "hook_context": "Validated through improved heuristic analysis",
        "confidence": final_confidence,
        "tokens_used": 0,
        "dimensions": {
            "performance": final_score * 0.85,
            "novelty": final_score * 0.9,
            "efficiency": final_score * 0.75,
            "safety": final_score * 1.05
        }
    }


async def send_to_observability_system(data: Dict[str, Any]) -> bool:
    """Send enhanced data to existing Vue.js observability system."""
    
    try:
        import httpx
        
        # Send via HTTP POST directly to the server endpoint
        http_url = "http://localhost:4000/events"
        
        # Transform data to HookEvent format for the API
        event_data = {
            "source_app": data.get("source_app") or "cc-hook-multi-agent-obvs",
            "session_id": data.get("session_id", "unknown"),
            "hook_event_type": data.get("hook_event_name", "PostToolUse"),
            "payload": data,  # Include full enhanced data with agent_context
            "timestamp": data.get("enhanced_timestamp") or int(time.time() * 1000)
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(http_url, json=event_data)
            if response.status_code == 200:
                return True
            else:
                print(f"HTTP POST failed: {response.status_code}", file=sys.stderr)
                return False
            
    except Exception as e:
        print(f"HTTP POST error: {e}", file=sys.stderr)
        
        # Fallback to file-based communication if HTTP unavailable
        try:
            observability_dir = Path.cwd() / "apps" / "server" / "data"
            observability_dir.mkdir(parents=True, exist_ok=True)
            
            event_file = observability_dir / "task_completion_events.json"
            
            events = []
            if event_file.exists():
                with open(event_file, 'r') as f:
                    events = json.load(f)
            
            events.append(data)
            
            # Keep only last 100 events
            events = events[-100:]
            
            with open(event_file, 'w') as f:
                json.dump(events, f, indent=2)
            
            return True
        except Exception:
            return False


async def main_async():
    """Main async function with FASE 5 enhanced model detection."""
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract session_id and enhance with agent context
        session_id = input_data.get('session_id', 'unknown')
        agent_context = get_current_agent_context()
        
        # FASE 5: Enhanced model detection with intelligent fallbacks
        model_info = detect_current_model(input_data)
        
        # ENHANCED: Extract unified metadata (replaces extract_proxy_metadata)
        unified_metadata = extract_unified_metadata(input_data)
        
        # WORKFLOW CONTEXT: Enhance with workflow context for Shrimp and Cipher events
        workflow_enhanced_data = enhance_with_workflow_context(input_data)
        
        # Enhance input data with comprehensive metadata
        enhanced_data = {
            **workflow_enhanced_data,  # Use workflow-enhanced data as base
            "agent_context": agent_context,
            "model_info": model_info,  # Now ENHANCED - includes intelligent fallbacks
            "enhanced_timestamp": int(time.time() * 1000),
            **unified_metadata  # Add complete event classification metadata
        }
        
        # === RATE LIMIT DETECTION ===
        # Check for rate limit messages in tool responses or error messages
        rate_limit_detected = False
        error_messages = []
        
        # Extract potential error messages from various sources
        if input_data.get('tool_response'):
            tool_response = input_data['tool_response']
            
            # Check stderr for rate limit messages
            if isinstance(tool_response, dict) and tool_response.get('stderr'):
                error_messages.append(tool_response['stderr'])
            
            # Check stdout for error patterns (some tools output errors to stdout)
            if isinstance(tool_response, dict) and tool_response.get('stdout'):
                stdout = tool_response['stdout']
                if any(keyword in stdout.lower() for keyword in ['rate limit', 'too many requests', 'quota exceeded']):
                    error_messages.append(stdout)
            
            # Check if tool_response itself is an error string
            if isinstance(tool_response, str) and any(keyword in tool_response.lower() for keyword in ['rate limit', 'error', 'failed']):
                error_messages.append(tool_response)
        
        # Check top-level error fields
        if input_data.get('error'):
            error_messages.append(input_data['error'])
        
        # Parse each error message for rate limit information
        for error_msg in error_messages:
            if error_msg and isinstance(error_msg, str):
                rate_limit_data = parse_and_store_rate_limit(error_msg, session_id)
                if rate_limit_data:
                    rate_limit_detected = True
                    enhanced_data["rate_limit_detected"] = True
                    enhanced_data["rate_limit_info"] = rate_limit_data
                    print(f"🚫 Rate limit detected: {rate_limit_data['provider']} - reset in {rate_limit_data.get('reset_seconds', 'unknown')}s", file=sys.stderr)
                    break
        
        # === CONTINUOUS OPERATIONS MANAGEMENT ===
        if CONTINUOUS_OPS_AVAILABLE and rate_limit_detected:
            try:
                # Initialize continuous operations manager if rate limit detected
                smart_router = SmartAPIRouter()
                continuous_manager = ContinuousOperationManager(smart_router)
                
                # Schedule auto-resume based on rate limit data
                if enhanced_data.get("rate_limit_info"):
                    reset_seconds = enhanced_data["rate_limit_info"].get("reset_seconds", 60)
                    if isinstance(reset_seconds, (int, float)) and reset_seconds > 0:
                        await continuous_manager.schedule_auto_resume(session_id, reset_seconds)
                        print(f"⏰ Continuous operations: Auto-resume scheduled for {session_id} in {reset_seconds}s", file=sys.stderr)
                        
                        # Update session state to rate limited
                        continuous_manager._update_session_state(
                            session_id,
                            continuous_manager.SessionState.RATE_LIMITED,
                            metadata={
                                'rate_limit_provider': enhanced_data["rate_limit_info"].get('provider'),
                                'rate_limit_reset': reset_seconds,
                                'detected_at': time.time()
                            }
                        )
                        enhanced_data["continuous_ops_scheduled"] = True
                        
            except Exception as e:
                print(f"⚠️ Continuous operations error: {e}", file=sys.stderr)
                enhanced_data["continuous_ops_error"] = str(e)
        
        # === TASK COMPLETION MONITORING ===
        task_completed = is_task_completion_event(input_data)
        primary_agent_active = is_primary_agent_active()
        
        # Record validation telemetry if advanced system is available
        if ADVANCED_VALIDATION_AVAILABLE:
            record_validation_event(enhanced_data)
        
        # If task completion detected, trigger enhanced workflows
        if task_completed:
            print(f"🎯 Task completion detected: {input_data.get('request', {}).get('tool_name', 'unknown')}", 
                  file=sys.stderr)
            
            # Trigger enhanced memory sync
            memory_sync_success = await trigger_enhanced_memory_sync(input_data)
            enhanced_data["memory_sync_triggered"] = memory_sync_success
            
            # Trigger ensemble validation if applicable
            if primary_agent_active or task_completed:
                ensemble_result = await trigger_ensemble_validation(input_data)
                enhanced_data["ensemble_validation"] = ensemble_result
                
                # Enhanced status reporting with event classification info
                if isinstance(ensemble_result, dict) and "consensus_score" in ensemble_result:
                    status = ensemble_result.get('final_status', 'unknown')
                    score = ensemble_result.get('consensus_score', 0)
                    models = len(ensemble_result.get('models_used', []))
                    event_type = enhanced_data.get('event_classification', 'unknown')
                    
                    if ADVANCED_VALIDATION_AVAILABLE and ensemble_result.get("ensemble_validation") == "advanced_collective_intelligence":
                        print(f"🧠 Advanced validation ({event_type}): {status} (score: {score:.1f}, {models} models)", file=sys.stderr)
                    else:
                        print(f"🔍 Ensemble validation ({event_type}): {status} (score: {score:.1f})", file=sys.stderr)
        
        # === EXISTING LOG FUNCTIONALITY (PRESERVED) ===
        # Ensure session log directory exists
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / 'post_tool_use.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append enhanced data instead of raw input_data
        log_data.append(enhanced_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # === ENHANCED OBSERVABILITY INTEGRATION ===
        # Send ALL tool usage to observability system with enhanced classification
        observability_success = await send_to_observability_system(enhanced_data)
        if observability_success:
            event_type = enhanced_data.get('event_classification', 'unknown')
            model_display = model_info if model_info != "unknown" else "enhanced-fallback"
            print(f"📊 Observability data sent ({event_type}, model: {model_display})", file=sys.stderr)
        else:
            print("⚠️ Failed to send observability data", file=sys.stderr)
        
        # === ADVANCED TELEMETRY DASHBOARD ===
        if ADVANCED_VALIDATION_AVAILABLE and task_completed:
            try:
                dashboard = get_validation_dashboard()
                recent_discoveries = len(dashboard.get("recent_discoveries", []))
                if recent_discoveries > 0:
                    print(f"🔬 {recent_discoveries} validation discoveries recorded", file=sys.stderr)
            except Exception as e:
                print(f"⚠️ Telemetry dashboard error: {e}", file=sys.stderr)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        print("⚠️ JSON decode error in post_tool_use hook", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        # Log error but exit cleanly to avoid breaking Claude Code
        print(f"⚠️ Post-tool-use hook error: {e}", file=sys.stderr)
        sys.exit(0)
    finally:
        # Cleanup telemetry if available
        if ADVANCED_VALIDATION_AVAILABLE:
            try:
                await cleanup_validation_telemetry()
            except Exception as e:
                print(f"⚠️ Telemetry cleanup error: {e}", file=sys.stderr)


def main():
    """Sync wrapper for async main function."""
    try:
        # Check if event loop exists
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, create new thread
                import threading
                import concurrent.futures
                
                def run_async():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    return new_loop.run_until_complete(main_async())
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async)
                    future.result(timeout=30)  # 30 second timeout
            else:
                loop.run_until_complete(main_async())
        except RuntimeError:
            # No event loop exists, create new one
            asyncio.run(main_async())
    
    except Exception as e:
        print(f"⚠️ Hook execution error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == '__main__':
    main()