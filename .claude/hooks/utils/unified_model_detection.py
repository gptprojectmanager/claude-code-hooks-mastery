#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///

"""
Unified Model Detection System
===============================

Centralized model detection logic that can be used by ALL Claude Code hooks
to ensure consistent model_info detection across the entire system.

This module extracts the proven model detection logic from post_tool_use.py
and makes it available to all hooks (pre_tool_use, user_prompt_submit, etc.)
"""

import json
import re
import sys
import time
from typing import Dict, Any, Optional, Tuple


def detect_litellm_proxy_usage(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Detect if liteLLM proxy is being used for this request.
    
    Args:
        payload: The complete JSON payload from stdin
        
    Returns:
        Tuple[bool, Optional[Dict]]: (is_proxy, proxy_info_dict)
    """
    
    proxy_indicators = [
        'localhost:4001', 'litellm', '127.0.0.1:4001',
        'http://localhost:4001', 'https://localhost:4001'
    ]
    
    # Check payload string for proxy indicators
    payload_str = json.dumps(payload).lower()
    for indicator in proxy_indicators:
        if indicator in payload_str:
            return True, {"proxy_type": "litellm", "api_type": "proxy_gemini"}
    
    # Check tool_response.stdout for liteLLM monitor data
    tool_response = payload.get('tool_response', {})
    if isinstance(tool_response, dict):
        stdout = tool_response.get('stdout', '')
        if stdout and 'litellm-monitor' in stdout:
            model_info = extract_model_from_litellm_stdout(stdout)
            if model_info:
                return True, {"extracted_model": model_info}
    
    return False, None


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
        model_patterns = [
            r'"model_info"\s*:\s*"([^"]*gemini[^"]*)"',
            r"'model_info'\s*:\s*'([^']*gemini[^']*)'",
            r'model_info["\']?\s*[:=]\s*["\']?([^"\',]*gemini[^"\',]*)["\']?'
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, stdout, re.IGNORECASE)
            if matches:
                model_info = matches[0]
                if "provider:gemini" in model_info:
                    return model_info
        
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
                return f"provider:gemini,model:{matches[0]},api:direct"
                
    except Exception as e:
        print(f"⚠️ Error extracting model from liteLLM stdout: {e}", file=sys.stderr)
    
    return None


def detect_embedded_gemini_events(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Detect Gemini API events embedded in tool_response.stdout that are NOT proxy calls.
    
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
        
        # Pattern: Look for Gemini model names in stdout text
        gemini_model_patterns = [
            r'gemini-2\.5-pro',
            r'gemini-2\.5-flash',
            r'gemini-pro',
            r'gemini-flash'
        ]
        
        for pattern in gemini_model_patterns:
            if re.search(pattern, stdout, re.IGNORECASE):
                return True, {
                    "event_type": "direct_gemini_api",
                    "api_type": "direct_gemini", 
                    "provider": "google_ai_studio",
                    "model": re.search(pattern, stdout, re.IGNORECASE).group(0),
                    "proxy_type": "none",
                    "source": "stdout_pattern"
                }
        
    except Exception as e:
        print(f"⚠️ Error detecting embedded Gemini events: {e}", file=sys.stderr)
    
    return False, None


def classify_event_source(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify the source of an event and extract metadata.
    
    Args:
        payload: The complete JSON payload
        
    Returns:
        Dict containing event classification and metadata
    """
    
    # Check for liteLLM proxy usage first
    is_proxy, proxy_info = detect_litellm_proxy_usage(payload)
    if is_proxy:
        result = {
            "event_classification": "litellm_proxy",
            "proxy_type": "litellm",
            "api_type": "proxy_gemini",
            "provider": "gemini"
        }
        if proxy_info and "extracted_model" in proxy_info:
            result["extracted_model"] = proxy_info["extracted_model"]
        return result
    
    # Check for direct Gemini API usage
    is_gemini, gemini_info = detect_embedded_gemini_events(payload)
    if is_gemini and gemini_info:
        return {
            "event_classification": "direct_gemini_api",
            "proxy_type": "none",
            "api_type": "direct_gemini",
            "provider": "gemini",
            "model": gemini_info.get("model", "gemini-2.5-pro"),
            "model_version": gemini_info.get("model_version", "2.5-pro")
        }
    
    # Check for Claude/Anthropic API patterns
    claude_model = extract_claude_model_from_payload(payload)
    if claude_model:
        return {
            "event_classification": "direct_anthropic_api",
            "proxy_type": "none", 
            "api_type": "direct_anthropic",
            "provider": "anthropic",
            "model": claude_model
        }
    
    # Default: Unknown source
    return {
        "event_classification": "unknown",
        "proxy_type": "unknown",
        "api_type": "unknown",
        "provider": "unknown"
    }


def extract_claude_model_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract Claude model information (opus, sonnet, haiku) from payload.
    """
    
    if not isinstance(payload, dict):
        return None
    
    # Method 1: Direct model fields in payload
    direct_fields = [
        'model', 'model_id', 'model_name', 'claude_model', 
        'anthropic_model', 'ai_model', 'llm_model', 'current_model'
    ]
    
    for field in direct_fields:
        if field in payload and payload[field]:
            model = _extract_claude_model_from_string(str(payload[field]))
            if model:
                return model
    
    # Method 2: Model information in request context  
    request = payload.get('request', {})
    if isinstance(request, dict):
        for field in direct_fields:
            if field in request and request[field]:
                model = _extract_claude_model_from_string(str(request[field]))
                if model:
                    return model
    
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


def extract_unified_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from payload for observability.
    
    Args:
        payload: The complete JSON payload
        
    Returns:
        Dict containing all extracted metadata
    """
    
    event_source = classify_event_source(payload)
    
    metadata = {
        "event_classification": event_source["event_classification"],
        "proxy_type": event_source.get("proxy_type"),
        "api_type": event_source.get("api_type"),
        "provider": event_source.get("provider"),
        "timestamp": int(time.time() * 1000)
    }
    
    # Add model-specific metadata
    if "extracted_model" in event_source:
        metadata["model_info"] = event_source["extracted_model"]
    elif "model" in event_source:
        metadata["model_info"] = event_source["model"]
    else:
        metadata["model_info"] = "unknown"
    
    return metadata


def detect_current_model(payload: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    MAIN MODEL DETECTION ENTRY POINT - Unified across all hooks.
    
    This function provides deterministic model detection that can be used
    by any Claude Code hook (post_tool_use, pre_tool_use, user_prompt_submit, etc.)
    
    Args:
        payload: Optional JSON payload from stdin. If provided, will be analyzed.
    
    Returns:
        The detected model name or "unknown" if no model data found.
    """
    
    if payload is None:
        print("⚠️ No payload provided for model detection", file=sys.stderr)
        return "unknown"
    
    # Use unified extraction method
    metadata = extract_unified_metadata(payload)
    model_info = metadata.get("model_info", "unknown")
    
    if model_info and model_info != "unknown":
        print(f"🎯 Unified model detected: {model_info}", file=sys.stderr)
        return model_info
    
    print("⚠️ Unified model detection returned unknown", file=sys.stderr)
    return "unknown"


def enhance_payload_with_model_detection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance any payload with unified model detection.
    
    This function can be called by ANY hook to add model detection
    to their event payload.
    
    Args:
        payload: Original payload from hook
        
    Returns:
        Enhanced payload with model_info and metadata
    """
    
    try:
        # Get unified metadata
        metadata = extract_unified_metadata(payload)
        
        # Enhance the payload
        enhanced_payload = {
            **payload,
            "model_info": metadata.get("model_info", "unknown"),
            "proxy_type": metadata.get("proxy_type", "unknown"),
            "api_type": metadata.get("api_type", "unknown"),
            "provider": metadata.get("provider", "unknown"),
            "event_classification": metadata.get("event_classification", "unknown"),
            "enhanced_timestamp": metadata.get("timestamp"),
            "model_detection_version": "unified_v1.0"
        }
        
        print(f"✅ Enhanced payload with model: {metadata.get('model_info')}", file=sys.stderr)
        return enhanced_payload
        
    except Exception as e:
        print(f"⚠️ Error enhancing payload: {e}", file=sys.stderr)
        # Return original payload with minimal enhancement
        return {
            **payload,
            "model_info": "unknown",
            "proxy_type": "unknown",
            "enhanced_timestamp": int(time.time() * 1000),
            "model_detection_error": str(e)
        }


if __name__ == "__main__":
    # Test the unified model detection system
    test_payloads = [
        {"tool_name": "Bash", "tool_response": {"stdout": "test"}},
        {"request": {"model": "claude-3.5-sonnet"}, "tool_name": "Read"},
        {"tool_response": {"stdout": '{"model_info":"provider:gemini,version:2.5-pro,model:gemini-2.5-pro"}'}}
    ]
    
    print("🧪 Testing Unified Model Detection System")
    for i, payload in enumerate(test_payloads):
        result = detect_current_model(payload)
        enhanced = enhance_payload_with_model_detection(payload)
        print(f"Test {i+1}: {result} | Enhanced: {enhanced.get('model_info')}")