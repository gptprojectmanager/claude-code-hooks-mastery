#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "python-dotenv",
# ]
# ///

"""
Observability Event Sender for Multi-Agent System

Sends hook events to observability server with agent metadata
for real-time monitoring of the 14 Claude Code sub-agents.
"""

import json
import os
import requests
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import agent detection utility
sys.path.append(str(Path(__file__).parent))
try:
    from agent_detector import get_current_agent_context
except ImportError:
    def get_current_agent_context():
        return {
            'agent_name': 'primary-agent',
            'agent_role': 'orchestrator', 
            'agent_category': 'core_development',
            'delegation_chain': 'primary-agent'
        }


class ObservabilityConfig:
    """Configuration for observability server connection."""
    
    def __init__(self):
        self.server_url = os.getenv('OBSERVABILITY_SERVER_URL', 'http://localhost:3000')
        self.api_key = os.getenv('OBSERVABILITY_API_KEY', '')
        self.enabled = os.getenv('OBSERVABILITY_ENABLED', 'true').lower() == 'true'
        self.timeout = int(os.getenv('OBSERVABILITY_TIMEOUT', '5'))
        
        # Support alternative port configurations
        port = os.getenv('OBSERVABILITY_PORT')
        if port:
            base_url = self.server_url.split(':')[:-1]
            self.server_url = f"{':'.join(base_url)}:{port}"


def send_observability_event(
    event_type: str,
    payload: Dict[str, Any],
    session_id: str = "",
    source_app: str = "claude-code",
    agent_metadata: Optional[Dict[str, str]] = None
) -> bool:
    """
    Send an event to the observability server with agent metadata.
    
    Args:
        event_type: Type of hook event (SubagentStop, PreToolUse, etc.)
        payload: Event payload data
        session_id: Claude Code session identifier
        source_app: Source application name
        agent_metadata: Optional agent metadata (auto-detected if not provided)
        
    Returns:
        bool: True if event was sent successfully, False otherwise
    """
    
    config = ObservabilityConfig()
    
    if not config.enabled:
        return True  # Silently succeed if observability is disabled
    
    try:
        # Get current agent context if not provided
        if agent_metadata is None:
            agent_metadata = get_current_agent_context()
        
        # Build enhanced payload with agent metadata
        enhanced_payload = {
            **payload,
            'agent_metadata': agent_metadata,
            'observability_version': '2.0',
            'multi_agent_enabled': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Prepare the event data
        event_data = {
            'source_app': source_app,
            'session_id': session_id,
            'hook_event_type': event_type,
            'payload': enhanced_payload,
            'timestamp': int(datetime.utcnow().timestamp() * 1000)
        }
        
        # Add agent fields for database storage
        if agent_metadata:
            event_data['agent_name'] = agent_metadata.get('agent_name')
            event_data['agent_role'] = agent_metadata.get('agent_role')
            event_data['agent_category'] = agent_metadata.get('agent_category')
            event_data['delegation_chain'] = agent_metadata.get('delegation_chain')
        
        # Send to observability server
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Claude-Code-Hooks-MultiAgent/2.0'
        }
        
        if config.api_key:
            headers['Authorization'] = f'Bearer {config.api_key}'
        
        response = requests.post(
            f'{config.server_url}/api/events',
            json=event_data,
            headers=headers,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            return True
        else:
            # Log error but don't fail the hook
            error_log = {
                'error': 'Observability server error',
                'status_code': response.status_code,
                'response': response.text[:200],
                'event_type': event_type,
                'agent': agent_metadata.get('agent_name') if agent_metadata else 'unknown'
            }
            log_observability_error(error_log)
            return False
            
    except requests.exceptions.RequestException as e:
        # Network errors - log but don't fail
        error_log = {
            'error': 'Network error sending to observability server',
            'exception': str(e),
            'event_type': event_type,
            'agent': agent_metadata.get('agent_name') if agent_metadata else 'unknown'
        }
        log_observability_error(error_log)
        return False
        
    except Exception as e:
        # Any other errors - log but don't fail
        error_log = {
            'error': 'Unexpected error in observability sender',
            'exception': str(e),
            'event_type': event_type
        }
        log_observability_error(error_log)
        return False


def log_observability_error(error_data: Dict[str, Any]) -> None:
    """Log observability errors to local file for debugging."""
    
    try:
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        error_log_file = log_dir / 'observability_errors.json'
        
        # Read existing errors
        errors = []
        if error_log_file.exists():
            try:
                with open(error_log_file, 'r') as f:
                    errors = json.load(f)
            except json.JSONDecodeError:
                errors = []
        
        # Add timestamp to error
        error_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        errors.append(error_data)
        
        # Keep only last 100 errors
        errors = errors[-100:]
        
        # Write back to file
        with open(error_log_file, 'w') as f:
            json.dump(errors, f, indent=2)
            
    except Exception:
        # Fail silently - don't break hook execution for logging errors
        pass


def test_observability_connection() -> Dict[str, Any]:
    """Test connection to observability server."""
    
    config = ObservabilityConfig()
    
    test_result = {
        'server_url': config.server_url,
        'enabled': config.enabled,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if not config.enabled:
        test_result['status'] = 'disabled'
        test_result['message'] = 'Observability is disabled via configuration'
        return test_result
    
    try:
        response = requests.get(
            f'{config.server_url}/api/health',
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            test_result['status'] = 'connected'
            test_result['message'] = 'Successfully connected to observability server'
            test_result['server_response'] = response.json() if response.headers.get('content-type') == 'application/json' else response.text
        else:
            test_result['status'] = 'error'
            test_result['message'] = f'Server returned status {response.status_code}'
            test_result['response'] = response.text[:200]
            
    except requests.exceptions.RequestException as e:
        test_result['status'] = 'connection_failed'
        test_result['message'] = f'Failed to connect: {str(e)}'
        
    except Exception as e:
        test_result['status'] = 'error'
        test_result['message'] = f'Unexpected error: {str(e)}'
    
    return test_result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Observability Event Sender')
    parser.add_argument('--test', action='store_true', help='Test connection to observability server')
    parser.add_argument('--event-type', help='Event type to send')
    parser.add_argument('--payload', help='JSON payload to send')
    parser.add_argument('--session-id', default='test-session', help='Session ID')
    
    args = parser.parse_args()
    
    if args.test:
        result = test_observability_connection()
        print(json.dumps(result, indent=2))
    elif args.event_type:
        payload = {}
        if args.payload:
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError:
                print("Error: Invalid JSON payload")
                sys.exit(1)
        
        success = send_observability_event(
            event_type=args.event_type,
            payload=payload,
            session_id=args.session_id
        )
        
        print(f"Event sent: {'success' if success else 'failed'}")
    else:
        print("Use --test to test connection or --event-type to send an event")