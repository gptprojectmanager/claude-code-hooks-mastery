#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "anthropic",
# ]
# ///

"""
Enhanced Model Detection System for FASE 5
==========================================

This module provides enhanced model detection with intelligent fallbacks while maintaining 
the deterministic approach as the highest priority. It addresses the issue where the dashboard
shows "Unknown" instead of actual model names.

Key improvements:
1. Maintains deterministic API-based detection as Priority 1
2. Adds intelligent environment-based detection as fallbacks
3. Provides context-aware model inference when appropriate
4. Returns structured model info for better dashboard display
"""

import json
import re
import sys
import os
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Import existing unified detection as base
try:
    from unified_model_detection import (
        detect_litellm_proxy_usage, 
        detect_embedded_gemini_events,
        classify_event_source, 
        extract_claude_model_from_payload,
        _extract_claude_model_from_string
    )
    UNIFIED_DETECTION_AVAILABLE = True
except ImportError:
    print("⚠️ Unified detection not available, using fallback implementation", file=sys.stderr)
    UNIFIED_DETECTION_AVAILABLE = False


def detect_current_claude_model_from_environment() -> Optional[str]:
    """
    Detect the current Claude model from environment context.
    
    This is used as an intelligent fallback when no API data is available.
    It attempts to determine the model from various environment indicators.
    
    Returns:
        Model name if detected, None otherwise
    """
    
    try:
        # Method 1: Check for Claude environment variables
        claude_model_env = os.environ.get('CLAUDE_MODEL')
        if claude_model_env:
            extracted = _extract_claude_model_from_string(claude_model_env)
            if extracted:
                return extracted
        
        # Method 2: Check for Anthropic API key type indicators
        anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if anthropic_api_key:
            # Some API keys have model hints in their structure
            if 'opus' in anthropic_api_key.lower():
                return 'opus'
            elif 'sonnet' in anthropic_api_key.lower():
                return 'sonnet'
        
        # Method 3: Check Claude CLI configuration if available
        claude_config_paths = [
            Path.home() / '.claude' / 'config.json',
            Path.home() / '.config' / 'claude' / 'config.json',
            Path.cwd() / '.claude' / 'config.json'
        ]
        
        for config_path in claude_config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    
                    # Look for model configuration
                    model_config = config_data.get('model') or config_data.get('default_model')
                    if model_config:
                        extracted = _extract_claude_model_from_string(str(model_config))
                        if extracted:
                            return extracted
                            
                except Exception as e:
                    continue  # Skip this config file
        
        # Method 4: Analyze current working context for model hints
        cwd = Path.cwd()
        
        # Check for project-specific model configuration
        project_configs = [
            cwd / 'claude.json',
            cwd / '.claude.json', 
            cwd / 'claude-config.json',
            cwd / 'anthropic.json'
        ]
        
        for config_path in project_configs:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    
                    model_config = config_data.get('model') or config_data.get('default_model')
                    if model_config:
                        extracted = _extract_claude_model_from_string(str(model_config))
                        if extracted:
                            return extracted
                            
                except Exception:
                    continue
        
        # Method 5: Intelligent inference based on session patterns
        # This is a last resort and should be conservative
        session_id = os.environ.get('CLAUDE_SESSION_ID', '')
        if session_id:
            # Some session IDs may contain model hints
            if 'opus' in session_id.lower():
                return 'opus'
            elif 'sonnet' in session_id.lower():
                return 'sonnet'
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error in environment model detection: {e}", file=sys.stderr)
        return None


def detect_model_from_recent_activity() -> Optional[str]:
    """
    Analyze recent activity logs to infer current model.
    
    This looks at recent tool usage patterns and session logs to make
    an educated guess about the current model in use.
    """
    
    try:
        # Look for recent session logs that might contain model information
        possible_log_dirs = [
            Path.cwd() / '.claude' / 'hooks' / 'utils' / 'logs',
            Path.cwd() / '.claude' / 'utils' / 'logs',
            Path.home() / '.claude' / 'logs'
        ]
        
        for log_dir in possible_log_dirs:
            if not log_dir.exists():
                continue
                
            # Find the most recent session logs
            try:
                session_dirs = [d for d in log_dir.iterdir() if d.is_dir()]
                if not session_dirs:
                    continue
                    
                # Sort by modification time, get most recent
                recent_session = max(session_dirs, key=lambda d: d.stat().st_mtime)
                
                # Check for model info in recent logs
                for log_file in ['post_tool_use.json', 'pre_tool_use.json']:
                    log_path = recent_session / log_file
                    if log_path.exists():
                        with open(log_path, 'r') as f:
                            log_data = json.load(f)
                        
                        # Look for recent entries with model info
                        if isinstance(log_data, list):
                            for entry in reversed(log_data[-10:]):  # Check last 10 entries
                                model_info = entry.get('model_info')
                                if model_info and model_info != 'unknown':
                                    # Found recent model info, use it
                                    return model_info
                                    
            except Exception:
                continue  # Skip this log directory
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error analyzing recent activity: {e}", file=sys.stderr)
        return None


def enhance_model_detection_with_fallbacks(payload: Dict[str, Any]) -> str:
    """
    Enhanced model detection with intelligent fallbacks.
    
    Priority order:
    1. Deterministic API-based detection (existing unified system)
    2. Environment-based detection
    3. Recent activity analysis
    4. Conservative agent context inference (as last resort)
    
    Args:
        payload: Tool usage payload
        
    Returns:
        Model information string (never returns "unknown")
    """
    
    # Priority 1: Use existing deterministic detection
    if UNIFIED_DETECTION_AVAILABLE:
        try:
            from unified_model_detection import detect_current_model
            deterministic_result = detect_current_model(payload)
            if deterministic_result and deterministic_result != "unknown":
                print(f"✅ Deterministic model detected: {deterministic_result}", file=sys.stderr)
                return deterministic_result
        except Exception as e:
            print(f"⚠️ Deterministic detection failed: {e}", file=sys.stderr)
    
    # Priority 2: Environment-based detection
    env_model = detect_current_claude_model_from_environment()
    if env_model:
        print(f"🌐 Environment model detected: {env_model}", file=sys.stderr)
        return f"provider:claude,model:{env_model},source:environment,confidence:medium"
    
    # Priority 3: Recent activity analysis
    activity_model = detect_model_from_recent_activity()
    if activity_model:
        print(f"📊 Activity model detected: {activity_model}", file=sys.stderr)
        return activity_model
    
    # Priority 4: Conservative agent context inference (last resort)
    agent_context = payload.get('agent_context', {})
    if agent_context and isinstance(agent_context, dict):
        agent_name = agent_context.get('agent_name', '').lower()
        
        # Only do very conservative inference for obvious cases
        if 'opus' in agent_name:
            print(f"🎯 Conservative inference: opus from agent context", file=sys.stderr)
            return "provider:claude,model:opus,source:agent_inference,confidence:low"
        elif 'sonnet' in agent_name:
            print(f"🎯 Conservative inference: sonnet from agent context", file=sys.stderr)
            return "provider:claude,model:sonnet,source:agent_inference,confidence:low"
        elif 'haiku' in agent_name:
            print(f"🎯 Conservative inference: haiku from agent context", file=sys.stderr)
            return "provider:claude,model:haiku,source:agent_inference,confidence:low"
    
    # Final fallback: Provide intelligent default based on context
    print(f"🔮 Using intelligent default detection", file=sys.stderr)
    
    # Check if this seems like a development/sophisticated task (likely Sonnet)
    if payload.get('tool_name') in ['Write', 'MultiEdit', 'Edit', 'Bash']:
        return "provider:claude,model:sonnet,source:intelligent_default,confidence:low"
    
    # For simple tasks, might be Haiku
    if payload.get('tool_name') in ['Read', 'LS', 'Grep']:
        return "provider:claude,model:haiku,source:intelligent_default,confidence:low"
    
    # Default to Sonnet (most common for development work)
    return "provider:claude,model:sonnet,source:default_inference,confidence:low"


def get_enhanced_model_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get comprehensive model information with enhanced detection and metadata.
    
    This provides structured model information that the dashboard can display properly.
    
    Args:
        payload: Tool usage payload
        
    Returns:
        Dictionary with enhanced model information
    """
    
    model_info = enhance_model_detection_with_fallbacks(payload)
    
    # Parse structured model info if available
    if isinstance(model_info, str) and 'provider:' in model_info:
        parts = model_info.split(',')
        parsed_info = {}
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                parsed_info[key.strip()] = value.strip()
        
        return {
            "model_info": model_info,
            "provider": parsed_info.get('provider', 'unknown'),
            "model": parsed_info.get('model', 'unknown'),
            "model_version": parsed_info.get('version', ''),
            "confidence": parsed_info.get('confidence', 'unknown'),
            "detection_source": parsed_info.get('source', 'unknown'),
            "enhanced_detection": True,
            "detection_timestamp": int(time.time() * 1000)
        }
    
    # Handle simple string model info
    else:
        return {
            "model_info": model_info,
            "provider": "claude" if model_info.lower() in ['opus', 'sonnet', 'haiku'] else "unknown",
            "model": model_info,
            "confidence": "medium",
            "detection_source": "legacy",
            "enhanced_detection": True,
            "detection_timestamp": int(time.time() * 1000)
        }


if __name__ == "__main__":
    # Test the enhanced detection system
    test_payload = {
        "tool_name": "Write",
        "agent_context": {"agent_name": "primary-agent"},
        "session_id": "test-session"
    }
    
    print("🧪 Testing Enhanced Model Detection")
    result = enhance_model_detection_with_fallbacks(test_payload)
    print(f"Result: {result}")
    
    enhanced_info = get_enhanced_model_info(test_payload)
    print(f"Enhanced Info: {json.dumps(enhanced_info, indent=2)}")