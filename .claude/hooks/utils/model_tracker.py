#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "asyncio",
# ]
# ///

"""
Model Tracker for Claude Code Session Context

Tracks the currently active AI model (Haiku, Sonnet, Opus, OpusPlan) 
across all hook events to enable comprehensive model display in observability.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any


class ModelTracker:
    """Session-based model tracking for Claude Code."""
    
    def __init__(self):
        self.session_file = Path.cwd() / '.claude' / 'session_model_context.json'
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure session file exists
        if not self.session_file.exists():
            self._init_session_file()
    
    def _init_session_file(self):
        """Initialize session tracking file."""
        initial_data = {
            "current_model": None,
            "last_updated": int(time.time() * 1000),
            "session_start": int(time.time() * 1000),
            "model_history": [],
            "event_count": 0
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    def update_model(self, model_info: Dict[str, str]) -> bool:
        """
        Update the current active model.
        
        Args:
            model_info: Dict with 'model' and 'agent_name' keys
            
        Returns:
            bool: True if model was updated, False if same as current
        """
        try:
            # Read current session data
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            current_model = session_data.get('current_model')
            new_model = model_info.get('model')
            
            # Only update if model actually changed
            if current_model != new_model:
                session_data['current_model'] = new_model
                session_data['last_updated'] = int(time.time() * 1000)
                session_data['event_count'] += 1
                
                # Add to history
                history_entry = {
                    "model": new_model,
                    "agent_name": model_info.get('agent_name'),
                    "timestamp": int(time.time() * 1000),
                    "event_count": session_data['event_count']
                }
                
                session_data['model_history'].append(history_entry)
                
                # Keep only last 50 history entries
                session_data['model_history'] = session_data['model_history'][-50:]
                
                # Write back to file
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Model tracker update error: {e}", file=sys.stderr)
            return False
    
    def get_current_model(self) -> Optional[str]:
        """Get the currently active model."""
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            return session_data.get('current_model')
            
        except Exception:
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information for current session."""
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            current_model = session_data.get('current_model')
            
            if current_model:
                return {
                    "model": current_model,
                    "emoji": self._get_model_emoji(current_model),
                    "display_name": self._get_model_display_name(current_model),
                    "last_updated": session_data.get('last_updated'),
                    "session_duration": int(time.time() * 1000) - session_data.get('session_start', 0),
                    "model_switches": len(session_data.get('model_history', [])),
                    "confidence": "high"  # High confidence since we're tracking explicitly
                }
            
            return {}
            
        except Exception:
            return {}
    
    def _get_model_emoji(self, model: str) -> str:
        """Get emoji for model type."""
        emoji_map = {
            'haiku': '🌸',
            'sonnet': '📝', 
            'opus': '👑',
            'opusplan': '📋'
        }
        return emoji_map.get(model.lower(), '🤖')
    
    def _get_model_display_name(self, model: str) -> str:
        """Get display name for model."""
        name_map = {
            'haiku': 'Haiku',
            'sonnet': 'Sonnet',
            'opus': 'Opus', 
            'opusplan': 'OpusPlan'
        }
        return name_map.get(model.lower(), model.title())
    
    def extract_model_from_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract model information from various event types.
        
        Supports:
        - Task tool events with subagent_type
        - Agent command events
        - Session context events
        """
        
        # Method 1: Direct subagent_type in Task events
        subagent_type = event_data.get('request', {}).get('parameters', {}).get('subagent_type')
        if subagent_type and isinstance(subagent_type, str):
            model = self._extract_model_from_subagent(subagent_type)
            if model:
                return {"model": model, "agent_name": subagent_type}
        
        # Method 2: Tool name patterns
        tool_name = event_data.get('request', {}).get('tool_name', '')
        if 'Task' in tool_name:
            # Check parameters for agent information
            params = event_data.get('request', {}).get('parameters', {})
            if 'subagent_type' in params:
                subagent = params['subagent_type']
                model = self._extract_model_from_subagent(subagent)
                if model:
                    return {"model": model, "agent_name": subagent}
        
        # Method 3: Check environment/session context
        session_id = event_data.get('session_id', '')
        if session_id:
            model = self._extract_model_from_session_id(session_id)
            if model:
                return {"model": model, "agent_name": f"session-{model}"}
        
        return None
    
    def _extract_model_from_subagent(self, subagent_type: str) -> Optional[str]:
        """Extract model from subagent type string."""
        if not isinstance(subagent_type, str):
            return None
        
        # Split by dash and check last part
        parts = subagent_type.split('-')
        if len(parts) >= 2:
            last_part = parts[-1].lower()
            if last_part in ['haiku', 'sonnet', 'opus', 'opusplan']:
                return last_part
        
        return None
    
    def _extract_model_from_session_id(self, session_id: str) -> Optional[str]:
        """Extract model from session ID patterns."""
        session_lower = session_id.lower()
        
        for model in ['opusplan', 'opus', 'sonnet', 'haiku']:  # Check opusplan first (longer match)
            if model in session_lower:
                return model
        
        return None
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session data."""
        try:
            current_time = int(time.time() * 1000)
            max_age_ms = max_age_hours * 60 * 60 * 1000
            
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            session_start = session_data.get('session_start', current_time)
            
            # If session is too old, reset it
            if current_time - session_start > max_age_ms:
                self._init_session_file()
                return True
            
            return False
            
        except Exception:
            return False


# Global instance
_model_tracker = None

def get_model_tracker() -> ModelTracker:
    """Get or create global model tracker instance."""
    global _model_tracker
    if _model_tracker is None:
        _model_tracker = ModelTracker()
    return _model_tracker


def track_model_from_event(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Track model from event and return current model info.
    
    This is the main function used by hooks to track and get model information.
    """
    tracker = get_model_tracker()
    
    # Try to extract model from current event
    model_info = tracker.extract_model_from_event(event_data)
    
    # Update tracker if we found new model info
    if model_info:
        tracker.update_model(model_info)
    
    # Return current model info (whether updated or existing)
    return tracker.get_model_info()


if __name__ == '__main__':
    import sys
    
    # Test functionality
    tracker = get_model_tracker()
    
    # Test model extraction
    test_event = {
        'request': {
            'tool_name': 'Task',
            'parameters': {
                'subagent_type': 'code-reviewer-opus'
            }
        }
    }
    
    model_info = track_model_from_event(test_event)
    print(json.dumps(model_info, indent=2))