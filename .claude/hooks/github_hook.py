#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "asyncio",
#     "aiohttp",
#     "python-dotenv",
#     "typing-extensions",
# ]
# ///

"""
GitHub Event Hook Processor

Webhook receiver che integra GitHub events nel sistema hooks esistente
mantenendo backward compatibility e consistency con send_event.py pattern.

Features:
- Webhook event processing con signature validation
- Integration con GitHubService per API operations
- Event routing tramite EventBus
- Orchestration tramite PrimaryAgentGitHubController
- Observability integration con existing pattern
"""

import asyncio
import json
import os
import sys
import logging
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import components seguendo existing architecture
sys.path.append(str(Path(__file__).parent))

# Initialize component classes as None for safe fallback
GitHubService = None
GitHubConfig = None
GitHubAPIError = None
GitHubEventBus = None 
GitHubEvent = None
PrimaryAgentGitHubController = None

# Try to import components individually with specific error handling
try:
    from github_service import GitHubService, GitHubConfig, GitHubAPIError
except ImportError as e:
    print(f"Info: GitHub service not available: {e}", file=sys.stderr)

try:
    from event_bus import GitHubEventBus, GitHubEvent
except ImportError as e:
    print(f"Info: Event bus not available: {e}", file=sys.stderr)

try:
    from primary_agent_github import PrimaryAgentGitHubController
except ImportError as e:
    print(f"Info: Primary agent controller not available (expected): {e}", file=sys.stderr)

# Import utilities
sys.path.append(str(Path(__file__).parent / "utils"))
try:
    from constants import ensure_session_log_dir, get_session_log_dir
    from observability_sender import send_observability_event
except ImportError:
    def ensure_session_log_dir(session_id: str) -> Path:
        log_dir = Path("logs") / session_id
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def get_session_log_dir(session_id: str) -> Path:
        return Path("logs") / session_id
        
    def send_observability_event(event_type: str, payload: Dict[str, Any], **kwargs) -> bool:
        return True
class GitHubWebhookConfig:
    """Configuration for GitHub webhook processing."""
    
    def __init__(self):
        # Webhook configuration
        self.webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
        self.webhook_enabled = os.getenv('GITHUB_WEBHOOK_ENABLED', 'true').lower() == 'true'
        
        # Processing configuration
        self.process_timeout = int(os.getenv('GITHUB_WEBHOOK_TIMEOUT', '30'))
        self.max_payload_size = int(os.getenv('GITHUB_MAX_PAYLOAD_SIZE', '10485760'))  # 10MB
        
        # Session configuration - consistent with existing hooks
        self.session_id = os.getenv('CLAUDE_SESSION_ID', 'default-session')
        
        # Event filtering
        self.enabled_events = set(os.getenv('GITHUB_WEBHOOK_EVENTS', 'push,pull_request,issues').split(','))
        
        # Integration settings
        self.observability_enabled = os.getenv('GITHUB_OBSERVABILITY_ENABLED', 'true').lower() == 'true'
        self.agent_orchestration = os.getenv('GITHUB_AGENT_ORCHESTRATION', 'true').lower() == 'true'


class GitHubWebhookValidator:
    """Validates GitHub webhook signatures and payloads."""
    
    def __init__(self, config: GitHubWebhookConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_signature(self, payload_body: str, signature: str) -> bool:
        """
        Validate GitHub webhook signature.
        
        Args:
            payload_body: Raw payload body
            signature: X-Hub-Signature-256 header value
            
        Returns:
            bool: True if signature is valid
        """
        if not self.config.webhook_secret:
            self.logger.warning("No webhook secret configured - skipping signature validation")
            return True
        
        if not signature:
            self.logger.error("No signature provided in webhook")
            return False
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            self.config.webhook_secret.encode('utf-8'),
            payload_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Secure comparison
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            self.logger.error("Invalid webhook signature")
        
        return is_valid    
    def validate_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate webhook payload structure.
        
        Args:
            payload: Parsed webhook payload
            
        Returns:
            bool: True if payload is valid
        """
        # Check required fields based on GitHub webhook spec
        required_fields = ['action', 'repository']
        
        for field in required_fields:
            if field not in payload:
                self.logger.error(f"Missing required field in webhook payload: {field}")
                return False
        
        # Validate repository structure
        repo = payload.get('repository', {})
        if not isinstance(repo, dict) or 'full_name' not in repo:
            self.logger.error("Invalid repository structure in webhook payload")
            return False
        
        return True


class GitHubEventProcessor:
    """Processes GitHub webhook events following existing hook patterns."""
    
    def __init__(self, config: GitHubWebhookConfig):
        self.config = config
        self.validator = GitHubWebhookValidator(config)
        self._setup_logging()
        
        # Initialize components if available
        self.github_service = None
        self.event_bus = None
        self.primary_controller = None
        
    def _setup_logging(self) -> None:
        """Setup logging following existing hook pattern."""
        log_dir = ensure_session_log_dir(self.config.session_id)
        log_file = log_dir / "github_hook.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)    
    async def _initialize_components(self) -> None:
        """Initialize GitHub components if available."""
        try:
            # Initialize GitHub Service if available
            if GitHubService is not None and GitHubConfig is not None:
                github_config = GitHubConfig()
                self.github_service = GitHubService(github_config)
                self.logger.info("GitHub Service initialized")
            
            # Initialize Event Bus if available
            if GitHubEventBus is not None:
                self.event_bus = GitHubEventBus()
                await self.event_bus.initialize()
                self.logger.info("Event Bus initialized")
            
            # Initialize Primary Controller if orchestration enabled and available
            if self.config.agent_orchestration and PrimaryAgentGitHubController is not None:
                self.primary_controller = PrimaryAgentGitHubController()
                await self.primary_controller.initialize()
                self.logger.info("Primary Controller initialized")
                
            if any([self.github_service, self.event_bus, self.primary_controller]):
                self.logger.info("GitHub components partially initialized")
            else:
                self.logger.info("GitHub components not available - running in basic mode")
            
        except Exception as e:
            self.logger.warning(f"Could not initialize all GitHub components: {e}")
            # Continue with basic functionality
    
    async def process_webhook_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        delivery_id: Optional[str] = None,
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process GitHub webhook event following send_event.py pattern.
        
        Args:
            event_type: GitHub event type (push, pull_request, etc.)
            payload: Webhook payload
            delivery_id: GitHub delivery ID
            signature: Webhook signature
            
        Returns:
            Dict containing processing result
        """
        processing_start = datetime.utcnow()
        
        # Validate if enabled
        if not self.config.webhook_enabled:
            return {
                'status': 'disabled',
                'message': 'GitHub webhook processing is disabled'
            }
        
        # Event filtering
        if event_type not in self.config.enabled_events:
            return {
                'status': 'filtered',
                'message': f'Event type {event_type} not in enabled events'
            }
        
        self.logger.info(f"Processing GitHub webhook: {event_type} (delivery: {delivery_id})")        
        result = {
            'event_type': event_type,
            'delivery_id': delivery_id,
            'timestamp': processing_start.isoformat() + 'Z',
            'session_id': self.config.session_id
        }
        
        try:
            # Validate payload structure
            if not self.validator.validate_payload(payload):
                result['status'] = 'validation_failed'
                result['message'] = 'Invalid payload structure'
                return result
            
            # Initialize components
            await self._initialize_components()
            
            # Create standardized event data following send_event.py pattern
            event_data = {
                'source_app': 'cc-hook-github-webhook',
                'session_id': self.config.session_id,
                'hook_event_type': 'GitHubEvent',
                'github_event_type': event_type,
                'payload': {
                    'action': payload.get('action'),
                    'repository': {
                        'full_name': payload['repository']['full_name'],
                        'name': payload['repository']['name'],
                        'owner': payload['repository']['owner']['login']
                    },
                    'sender': payload.get('sender', {}).get('login'),
                    'delivery_id': delivery_id,
                    'raw_payload_keys': list(payload.keys())
                },
                'timestamp': int(processing_start.timestamp() * 1000)
            }
            
            # Process event through Event Bus if available
            if self.event_bus and GitHubEvent:
                try:
                    github_event = GitHubEvent(
                        event_type=event_type,
                        payload=payload,
                        source_repo=payload['repository']['full_name']
                    )
                    
                    await self.event_bus.publish_event(github_event)
                    result['event_bus'] = 'processed'
                except Exception as e:
                    self.logger.warning(f"Event bus processing failed: {e}")
                    result['event_bus'] = 'failed'            
            # Orchestrate through Primary Controller if available
            if self.primary_controller and self.config.agent_orchestration:
                try:
                    orchestration_result = await self.primary_controller.handle_github_event(
                        event_type=event_type,
                        payload=payload,
                        event_data=event_data
                    )
                    result['orchestration'] = orchestration_result
                except Exception as e:
                    self.logger.warning(f"Orchestration failed: {e}")
                    result['orchestration'] = {'status': 'failed', 'error': str(e)}
            
            # Send to observability following send_event.py pattern
            if self.config.observability_enabled:
                try:
                    observability_success = send_observability_event(
                        event_type='GitHubWebhook',
                        payload=event_data,
                        server_url=os.getenv('OBSERVABILITY_SERVER_URL', 'http://localhost:4000/events')
                    )
                    result['observability'] = 'sent' if observability_success else 'failed'
                except Exception as e:
                    self.logger.warning(f"Observability send failed: {e}")
                    result['observability'] = 'failed'
            
            # Calculate processing time
            processing_end = datetime.utcnow()
            processing_time = (processing_end - processing_start).total_seconds()
            
            result.update({
                'status': 'processed',
                'processing_time_seconds': processing_time,
                'components_used': {
                    'github_service': self.github_service is not None,
                    'event_bus': self.event_bus is not None,
                    'primary_controller': self.primary_controller is not None
                }
            })
            
            self.logger.info(f"GitHub webhook processed successfully: {event_type} in {processing_time:.3f}s")
            
        except Exception as e:
            self.logger.error(f"Error processing GitHub webhook: {e}")
            result.update({
                'status': 'error',
                'error': str(e)
            })
        
        return result    
    def _determine_event_priority(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Determine event priority based on type and content."""
        try:
            # Critical security or error events  
            if event_type in ['security_advisory', 'repository_vulnerability_alert']:
                return 'CRITICAL'
            
            # High priority events
            if event_type in ['pull_request'] and payload.get('action') in ['opened', 'synchronize']:
                return 'HIGH'
            
            # Medium priority events
            if event_type in ['issues', 'pull_request_review']:
                return 'MEDIUM'
            
            # Default to low priority
            return 'LOW'
            
        except Exception:
            return 'LOW'


def process_stdin_webhook() -> Dict[str, Any]:
    """
    Process webhook data from stdin following existing hook pattern.
    
    Returns:
        Dict containing processing result
    """
    try:
        # Read from stdin like other hooks
        input_data = json.load(sys.stdin)
        
        # Extract webhook data
        event_type = input_data.get('event_type', '')
        payload = input_data.get('payload', {})
        delivery_id = input_data.get('delivery_id')
        signature = input_data.get('signature')
        
        if not event_type or not payload:
            return {
                'status': 'error',
                'message': 'Missing event_type or payload in input'
            }
        
        # Process the event
        config = GitHubWebhookConfig()
        processor = GitHubEventProcessor(config)
        
        # Run async processing
        result = asyncio.run(
            processor.process_webhook_event(
                event_type=event_type,
                payload=payload,
                delivery_id=delivery_id,
                signature=signature
            )
        )
        
        return result
        
    except json.JSONDecodeError as e:
        return {
            'status': 'error',
            'message': f'Failed to parse JSON input: {e}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Processing failed: {e}'
        }

def main():
    """Main entry point with command line argument support."""
    parser = argparse.ArgumentParser(description='GitHub Webhook Event Processor')
    parser.add_argument('--stdin', action='store_true', 
                       help='Process webhook from stdin (default hook behavior)')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test GitHub service connection')
    parser.add_argument('--validate-config', action='store_true',
                       help='Validate webhook configuration')
    
    args = parser.parse_args()
    
    if args.test_connection:
        # Test GitHub service connection
        try:
            from github_service import test_github_connection
            result = asyncio.run(test_github_connection())
            print(json.dumps(result, indent=2))
        except ImportError:
            print(json.dumps({
                'status': 'error',
                'message': 'GitHub service not available'
            }, indent=2))
    
    elif args.validate_config:
        # Validate configuration
        config = GitHubWebhookConfig()
        validation_result = {
            'webhook_enabled': config.webhook_enabled,
            'webhook_secret_configured': bool(config.webhook_secret),
            'enabled_events': list(config.enabled_events),
            'observability_enabled': config.observability_enabled,
            'agent_orchestration': config.agent_orchestration,
            'session_id': config.session_id
        }
        print(json.dumps(validation_result, indent=2))
    
    else:
        # Default: process from stdin (standard hook behavior)
        result = process_stdin_webhook()
        
        # Print result to stdout for observability
        print(json.dumps(result, indent=2))
        
        # Always exit 0 to not block Claude Code operations (following send_event.py pattern)
        sys.exit(0)


if __name__ == '__main__':
    main()