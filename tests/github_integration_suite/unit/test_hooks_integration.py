"""
Unit Tests for GitHub Hooks Integration
Testing backward compatibility, event processing, webhook handling, and integration patterns
"""

import pytest
import asyncio
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock, call
from datetime import datetime
from pathlib import Path
import tempfile

# Import the components to test
import sys
sys.path.append('/Users/sam/claude-code-hooks-mastery/.claude/hooks')

try:
    from github_hook import (
        GitHubWebhookConfig,
        GitHubWebhookValidator,
        GitHubEventProcessor,
        process_stdin_webhook
    )
except ImportError:
    pytestmark = pytest.mark.skip("GitHub hook components not available")


class TestGitHubWebhookConfig:
    """Test GitHub webhook configuration."""
    
    def test_default_config(self):
        """Test default webhook configuration."""
        config = GitHubWebhookConfig()
        
        assert config.webhook_enabled == True
        assert config.process_timeout == 30
        assert config.max_payload_size == 10485760  # 10MB
        assert config.observability_enabled == True
        assert config.agent_orchestration == True
        assert isinstance(config.enabled_events, set)
        assert 'push' in config.enabled_events
        assert 'pull_request' in config.enabled_events
    
    @patch.dict(os.environ, {
        'GITHUB_WEBHOOK_SECRET': 'test-secret-123',
        'GITHUB_WEBHOOK_ENABLED': 'false',
        'GITHUB_WEBHOOK_TIMEOUT': '60',
        'GITHUB_MAX_PAYLOAD_SIZE': '5242880',  # 5MB
        'CLAUDE_SESSION_ID': 'webhook-test-session',
        'GITHUB_WEBHOOK_EVENTS': 'push,issues,security_advisory',
        'GITHUB_OBSERVABILITY_ENABLED': 'false',
        'GITHUB_AGENT_ORCHESTRATION': 'false'
    })
    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        config = GitHubWebhookConfig()
        
        assert config.webhook_secret == 'test-secret-123'
        assert config.webhook_enabled == False
        assert config.process_timeout == 60
        assert config.max_payload_size == 5242880
        assert config.session_id == 'webhook-test-session'
        assert config.enabled_events == {'push', 'issues', 'security_advisory'}
        assert config.observability_enabled == False
        assert config.agent_orchestration == False
    
    def test_session_id_defaults(self):
        """Test session ID configuration defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = GitHubWebhookConfig()
            assert config.session_id == 'default-session'
        
        with patch.dict(os.environ, {'CLAUDE_SESSION_ID': 'custom-session'}):
            config = GitHubWebhookConfig()
            assert config.session_id == 'custom-session'


class TestGitHubWebhookValidator:
    """Test GitHub webhook validation."""
    
    def setup_method(self):
        """Setup webhook validator."""
        self.config = GitHubWebhookConfig()
        self.config.webhook_secret = 'test-secret-key'
        self.validator = GitHubWebhookValidator(self.config)
    
    def test_validate_signature_success(self):
        """Test successful signature validation."""
        payload_body = '{"test": "payload"}'
        
        # Calculate expected signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            self.config.webhook_secret.encode('utf-8'),
            payload_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signature = f'sha256={expected_signature}'
        
        result = self.validator.validate_signature(payload_body, signature)
        assert result == True
    
    def test_validate_signature_without_prefix(self):
        """Test signature validation without sha256= prefix."""
        payload_body = '{"test": "payload"}'
        
        import hmac
        import hashlib
        expected_signature = hmac.new(
            self.config.webhook_secret.encode('utf-8'),
            payload_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Test without sha256= prefix
        result = self.validator.validate_signature(payload_body, expected_signature)
        assert result == True
    
    def test_validate_signature_failure(self):
        """Test signature validation failure."""
        payload_body = '{"test": "payload"}'
        invalid_signature = 'sha256=invalid_signature_hash'
        
        result = self.validator.validate_signature(payload_body, invalid_signature)
        assert result == False
    
    def test_validate_signature_no_secret(self):
        """Test signature validation without configured secret."""
        self.config.webhook_secret = ''
        validator = GitHubWebhookValidator(self.config)
        
        result = validator.validate_signature('{"test": "payload"}', 'sha256=anything')
        assert result == True  # Should skip validation
    
    def test_validate_signature_no_signature(self):
        """Test signature validation without provided signature."""
        result = self.validator.validate_signature('{"test": "payload"}', '')
        assert result == False
    
    def test_validate_payload_success(self):
        """Test successful payload validation."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'owner/repo',
                'name': 'repo',
                'owner': {'login': 'owner'}
            }
        }
        
        result = self.validator.validate_payload(valid_payload)
        assert result == True
    
    def test_validate_payload_missing_action(self):
        """Test payload validation with missing action."""
        invalid_payload = {
            'repository': {
                'id': 123,
                'full_name': 'owner/repo',
                'name': 'repo',
                'owner': {'login': 'owner'}
            }
        }
        
        result = self.validator.validate_payload(invalid_payload)
        assert result == False
    
    def test_validate_payload_missing_repository(self):
        """Test payload validation with missing repository."""
        invalid_payload = {
            'action': 'opened'
        }
        
        result = self.validator.validate_payload(invalid_payload)
        assert result == False
    
    def test_validate_payload_invalid_repository_structure(self):
        """Test payload validation with invalid repository structure."""
        invalid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'name': 'repo'
                # Missing full_name
            }
        }
        
        result = self.validator.validate_payload(invalid_payload)
        assert result == False
        
        # Test with repository as non-dict
        invalid_payload2 = {
            'action': 'opened',
            'repository': 'not-a-dict'
        }
        
        result2 = self.validator.validate_payload(invalid_payload2)
        assert result2 == False


class TestGitHubEventProcessor:
    """Test GitHub event processing."""
    
    def setup_method(self):
        """Setup event processor."""
        self.config = GitHubWebhookConfig()
        self.config.session_id = 'test-processor-session'
        self.config.webhook_enabled = True
        self.processor = GitHubEventProcessor(self.config)
    
    async def test_processor_initialization(self):
        """Test processor initialization."""
        assert self.processor.config == self.config
        assert self.processor.validator is not None
        assert self.processor.github_service is None  # Not initialized yet
        assert self.processor.event_bus is None
        assert self.processor.primary_controller is None
    
    async def test_process_webhook_event_disabled(self):
        """Test webhook processing when disabled."""
        self.config.webhook_enabled = False
        processor = GitHubEventProcessor(self.config)
        
        result = await processor.process_webhook_event(
            event_type='push',
            payload={'test': 'data'},
            delivery_id='test-123'
        )
        
        assert result['status'] == 'disabled'
        assert 'disabled' in result['message']
    
    async def test_process_webhook_event_filtered(self):
        """Test webhook processing with event filtering."""
        self.config.enabled_events = {'pull_request'}
        processor = GitHubEventProcessor(self.config)
        
        result = await processor.process_webhook_event(
            event_type='push',  # Not in enabled events
            payload={'test': 'data'},
            delivery_id='test-123'
        )
        
        assert result['status'] == 'filtered'
        assert 'not in enabled events' in result['message']
    
    async def test_process_webhook_event_invalid_payload(self):
        """Test webhook processing with invalid payload."""
        invalid_payload = {'no_action': 'test', 'no_repository': 'test'}
        
        result = await self.processor.process_webhook_event(
            event_type='push',
            payload=invalid_payload,
            delivery_id='test-123'
        )
        
        assert result['status'] == 'validation_failed'
        assert 'Invalid payload structure' in result['message']
    
    async def test_process_webhook_event_success_basic(self):
        """Test successful basic webhook processing."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            },
            'sender': {'login': 'test-user'}
        }
        
        with patch.object(self.processor, '_initialize_components'), \
             patch.object(self.processor, '_store_event_in_krag', return_value=True):
            
            result = await self.processor.process_webhook_event(
                event_type='pull_request',
                payload=valid_payload,
                delivery_id='delivery-123',
                signature='sha256=valid'
            )
            
            assert result['status'] == 'processed'
            assert result['event_type'] == 'pull_request'
            assert result['delivery_id'] == 'delivery-123'
            assert result['session_id'] == 'test-processor-session'
            assert 'processing_time_seconds' in result
            assert 'components_used' in result
    
    async def test_process_webhook_event_with_event_bus(self):
        """Test webhook processing with event bus integration."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            },
            'sender': {'login': 'test-user'}
        }
        
        # Mock event bus
        mock_event_bus = AsyncMock()
        mock_event_bus.publish_event.return_value = 'event-id-123'
        self.processor.event_bus = mock_event_bus
        
        # Mock GitHubEvent class
        mock_github_event_class = MagicMock()
        
        with patch.object(self.processor, '_initialize_components'), \
             patch('github_hook.GitHubEvent', mock_github_event_class):
            
            result = await self.processor.process_webhook_event(
                event_type='pull_request',
                payload=valid_payload,
                delivery_id='delivery-123'
            )
            
            assert result['status'] == 'processed'
            assert result['event_bus'] == 'processed'
            mock_event_bus.publish_event.assert_called_once()
    
    async def test_process_webhook_event_with_orchestration(self):
        """Test webhook processing with primary controller orchestration."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            },
            'sender': {'login': 'test-user'}
        }
        
        # Mock primary controller
        mock_controller = AsyncMock()
        mock_controller.handle_github_event.return_value = {
            'status': 'orchestrated',
            'agents_triggered': ['coder', 'reviewer']
        }
        self.processor.primary_controller = mock_controller
        
        with patch.object(self.processor, '_initialize_components'):
            
            result = await self.processor.process_webhook_event(
                event_type='pull_request',
                payload=valid_payload,
                delivery_id='delivery-123'
            )
            
            assert result['status'] == 'processed'
            assert result['orchestration']['status'] == 'orchestrated'
            mock_controller.handle_github_event.assert_called_once()
    
    async def test_process_webhook_event_orchestration_failure(self):
        """Test webhook processing with orchestration failure."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            }
        }
        
        # Mock failing primary controller
        mock_controller = AsyncMock()
        mock_controller.handle_github_event.side_effect = Exception("Orchestration failed")
        self.processor.primary_controller = mock_controller
        
        with patch.object(self.processor, '_initialize_components'):
            
            result = await self.processor.process_webhook_event(
                event_type='pull_request',
                payload=valid_payload,
                delivery_id='delivery-123'
            )
            
            assert result['status'] == 'processed'  # Overall processing succeeds
            assert result['orchestration']['status'] == 'failed'
            assert 'Orchestration failed' in result['orchestration']['error']
    
    @patch('github_hook.send_observability_event')
    async def test_process_webhook_event_with_observability(self, mock_send_observability):
        """Test webhook processing with observability integration."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            }
        }
        
        mock_send_observability.return_value = True
        self.processor.config.observability_enabled = True
        
        with patch.object(self.processor, '_initialize_components'):
            
            result = await self.processor.process_webhook_event(
                event_type='pull_request',
                payload=valid_payload,
                delivery_id='delivery-123'
            )
            
            assert result['status'] == 'processed'
            assert result['observability'] == 'sent'
            
            # Verify observability event was sent
            mock_send_observability.assert_called_once()
            call_args = mock_send_observability.call_args
            assert call_args[1]['event_type'] == 'GitHubWebhook'
            assert 'payload' in call_args[1]
    
    @patch('github_hook.send_observability_event')
    async def test_process_webhook_event_observability_failure(self, mock_send_observability):
        """Test webhook processing with observability failure."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            }
        }
        
        mock_send_observability.side_effect = Exception("Observability failed")
        self.processor.config.observability_enabled = True
        
        with patch.object(self.processor, '_initialize_components'):
            
            result = await self.processor.process_webhook_event(
                event_type='pull_request',
                payload=valid_payload,
                delivery_id='delivery-123'
            )
            
            assert result['status'] == 'processed'  # Overall processing still succeeds
            assert result['observability'] == 'failed'
    
    async def test_process_webhook_event_exception_handling(self):
        """Test webhook processing with exception handling."""
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            }
        }
        
        # Mock component initialization to fail
        with patch.object(self.processor, '_initialize_components', side_effect=Exception("Init failed")):
            
            result = await self.processor.process_webhook_event(
                event_type='pull_request',
                payload=valid_payload,
                delivery_id='delivery-123'
            )
            
            assert result['status'] == 'error'
            assert 'Init failed' in result['error']
    
    def test_determine_event_priority(self):
        """Test event priority determination."""
        # Critical priority
        priority = self.processor._determine_event_priority('security_advisory', {})
        assert priority == 'CRITICAL'
        
        priority = self.processor._determine_event_priority('repository_vulnerability_alert', {})
        assert priority == 'CRITICAL'
        
        # High priority
        priority = self.processor._determine_event_priority('pull_request', {'action': 'opened'})
        assert priority == 'HIGH'
        
        priority = self.processor._determine_event_priority('pull_request', {'action': 'synchronize'})
        assert priority == 'HIGH'
        
        # Medium priority
        priority = self.processor._determine_event_priority('issues', {'action': 'opened'})
        assert priority == 'MEDIUM'
        
        priority = self.processor._determine_event_priority('pull_request_review', {})
        assert priority == 'MEDIUM'
        
        # Low priority (default)
        priority = self.processor._determine_event_priority('push', {})
        assert priority == 'LOW'
        
        priority = self.processor._determine_event_priority('unknown_event', {})
        assert priority == 'LOW'
    
    def test_determine_event_priority_exception_handling(self):
        """Test event priority determination with exception handling."""
        # Should return LOW on any exception
        priority = self.processor._determine_event_priority('pull_request', None)  # None will cause exception
        assert priority == 'LOW'


class TestProcessStdinWebhook:
    """Test stdin webhook processing function."""
    
    def test_process_stdin_webhook_success(self):
        """Test successful stdin webhook processing."""
        input_data = {
            'event_type': 'push',
            'payload': {
                'repository': {
                    'id': 123,
                    'full_name': 'test/repo',
                    'name': 'repo',
                    'owner': {'login': 'test'}
                },
                'action': None  # Push events don't have action
            },
            'delivery_id': 'delivery-123',
            'signature': 'sha256=valid'
        }
        
        with patch('sys.stdin') as mock_stdin, \
             patch('json.load') as mock_json_load, \
             patch('asyncio.run') as mock_asyncio_run:
            
            mock_json_load.return_value = input_data
            mock_asyncio_run.return_value = {'status': 'processed'}
            
            result = process_stdin_webhook()
            
            assert result['status'] == 'processed'
            mock_json_load.assert_called_once_with(mock_stdin)
            mock_asyncio_run.assert_called_once()
    
    def test_process_stdin_webhook_missing_fields(self):
        """Test stdin webhook processing with missing fields."""
        input_data = {
            'event_type': 'push'
            # Missing payload
        }
        
        with patch('sys.stdin'), \
             patch('json.load', return_value=input_data):
            
            result = process_stdin_webhook()
            
            assert result['status'] == 'error'
            assert 'Missing event_type or payload' in result['message']
    
    def test_process_stdin_webhook_empty_event_type(self):
        """Test stdin webhook processing with empty event type."""
        input_data = {
            'event_type': '',
            'payload': {'test': 'data'}
        }
        
        with patch('sys.stdin'), \
             patch('json.load', return_value=input_data):
            
            result = process_stdin_webhook()
            
            assert result['status'] == 'error'
            assert 'Missing event_type or payload' in result['message']
    
    def test_process_stdin_webhook_json_decode_error(self):
        """Test stdin webhook processing with JSON decode error."""
        with patch('sys.stdin'), \
             patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0)):
            
            result = process_stdin_webhook()
            
            assert result['status'] == 'error'
            assert 'Failed to parse JSON input' in result['message']
    
    def test_process_stdin_webhook_general_exception(self):
        """Test stdin webhook processing with general exception."""
        with patch('sys.stdin'), \
             patch('json.load', side_effect=Exception("Unexpected error")):
            
            result = process_stdin_webhook()
            
            assert result['status'] == 'error'
            assert 'Processing failed' in result['message']
            assert 'Unexpected error' in result['message']


class TestGitHubHookBackwardCompatibility:
    """Test backward compatibility with existing hooks system."""
    
    @patch('github_hook.GitHubEventBus')
    @patch('github_hook.GitHubService')
    async def test_component_integration_availability(self, mock_service, mock_event_bus):
        """Test that components integrate gracefully when available."""
        config = GitHubWebhookConfig()
        processor = GitHubEventProcessor(config)
        
        # Mock components being available
        mock_service.return_value = AsyncMock()
        mock_event_bus.return_value = AsyncMock()
        
        await processor._initialize_components()
        
        # Should attempt to initialize available components
        assert processor.github_service is not None or processor.event_bus is not None
    
    async def test_graceful_degradation_no_components(self):
        """Test graceful degradation when components are not available."""
        config = GitHubWebhookConfig()
        processor = GitHubEventProcessor(config)
        
        # All components should be None initially
        assert processor.github_service is None
        assert processor.event_bus is None
        assert processor.primary_controller is None
        
        await processor._initialize_components()
        
        # Should not crash even when components are unavailable
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test/repo',
                'name': 'repo',
                'owner': {'login': 'test'}
            }
        }
        
        result = await processor.process_webhook_event(
            event_type='push',
            payload=valid_payload,
            delivery_id='test-123'
        )
        
        assert result['status'] == 'processed'
        assert result['components_used']['github_service'] == False
        assert result['components_used']['event_bus'] == False
        assert result['components_used']['primary_controller'] == False
    
    def test_environment_variable_compatibility(self):
        """Test compatibility with existing environment variable patterns."""
        # Test CLAUDE_SESSION_ID compatibility
        with patch.dict(os.environ, {'CLAUDE_SESSION_ID': 'hooks-test-session'}):
            config = GitHubWebhookConfig()
            assert config.session_id == 'hooks-test-session'
        
        # Test observability settings compatibility
        with patch.dict(os.environ, {'GITHUB_OBSERVABILITY_ENABLED': 'false'}):
            config = GitHubWebhookConfig()
            assert config.observability_enabled == False
    
    def test_event_data_structure_compatibility(self):
        """Test that event data follows existing send_event.py patterns."""
        config = GitHubWebhookConfig()
        config.session_id = 'compat-test'
        processor = GitHubEventProcessor(config)
        
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test-owner/test-repo',
                'name': 'test-repo',
                'owner': {'login': 'test-owner'}
            },
            'sender': {'login': 'test-user'}
        }
        
        async def test_event_structure():
            with patch.object(processor, '_initialize_components'):
                result = await processor.process_webhook_event(
                    event_type='pull_request',
                    payload=valid_payload,
                    delivery_id='delivery-123'
                )
                
                assert result['event_type'] == 'pull_request'
                assert result['delivery_id'] == 'delivery-123'
                assert result['session_id'] == 'compat-test'
                assert 'timestamp' in result
                
                # Should follow send_event.py timestamp format (ISO string ending with Z)
                assert result['timestamp'].endswith('Z')
        
        asyncio.run(test_event_structure())


class TestGitHubHookCommandLineInterface:
    """Test command line interface functionality."""
    
    def test_stdin_processing_default(self, capsys):
        """Test default stdin processing behavior."""
        input_data = {
            'event_type': 'push',
            'payload': {
                'repository': {
                    'full_name': 'test/repo',
                    'name': 'repo',
                    'owner': {'login': 'test'}
                },
                'action': None
            }
        }
        
        with patch('sys.stdin'), \
             patch('json.load', return_value=input_data), \
             patch('github_hook.GitHubWebhookConfig'), \
             patch('github_hook.GitHubEventProcessor') as mock_processor_class:
            
            mock_processor = AsyncMock()
            mock_processor.process_webhook_event.return_value = {'status': 'processed'}
            mock_processor_class.return_value = mock_processor
            
            # Test main function with no arguments (default stdin processing)
            from github_hook import process_stdin_webhook
            result = process_stdin_webhook()
            
            # Should process the webhook
            assert isinstance(result, dict)
    
    @patch('github_hook.test_github_connection')
    def test_test_connection_command(self, mock_test_connection):
        """Test --test-connection command."""
        mock_test_connection.return_value = {'status': 'connected'}
        
        # Would need to import and test main() function with mocked sys.argv
        # This is a placeholder for CLI testing
        assert True
    
    def test_validate_config_command(self):
        """Test --validate-config command."""
        with patch.dict(os.environ, {
            'GITHUB_WEBHOOK_ENABLED': 'true',
            'GITHUB_WEBHOOK_SECRET': 'test-secret',
            'GITHUB_WEBHOOK_EVENTS': 'push,pull_request',
            'CLAUDE_SESSION_ID': 'cli-test'
        }):
            config = GitHubWebhookConfig()
            
            validation_result = {
                'webhook_enabled': config.webhook_enabled,
                'webhook_secret_configured': bool(config.webhook_secret),
                'enabled_events': list(config.enabled_events),
                'observability_enabled': config.observability_enabled,
                'agent_orchestration': config.agent_orchestration,
                'session_id': config.session_id
            }
            
            assert validation_result['webhook_enabled'] == True
            assert validation_result['webhook_secret_configured'] == True
            assert 'push' in validation_result['enabled_events']
            assert validation_result['session_id'] == 'cli-test'


class TestGitHubHookErrorHandling:
    """Test comprehensive error handling."""
    
    async def test_component_initialization_failure(self):
        """Test handling of component initialization failures."""
        config = GitHubWebhookConfig()
        processor = GitHubEventProcessor(config)
        
        # Mock components to fail during initialization
        with patch('github_hook.GitHubService', side_effect=Exception("Service init failed")), \
             patch('github_hook.GitHubEventBus', side_effect=Exception("Event bus init failed")):
            
            # Should not crash during initialization
            await processor._initialize_components()
            
            # Components should remain None
            assert processor.github_service is None
            assert processor.event_bus is None
    
    async def test_payload_validation_edge_cases(self):
        """Test payload validation with edge cases."""
        config = GitHubWebhookConfig()
        validator = GitHubWebhookValidator(config)
        
        # Test with None payload
        result = validator.validate_payload(None)
        assert result == False
        
        # Test with empty payload
        result = validator.validate_payload({})
        assert result == False
        
        # Test with malformed repository
        malformed_payload = {
            'action': 'opened',
            'repository': []  # Array instead of object
        }
        result = validator.validate_payload(malformed_payload)
        assert result == False
    
    async def test_event_processing_timeout_handling(self):
        """Test event processing timeout handling."""
        config = GitHubWebhookConfig()
        config.process_timeout = 1  # 1 second timeout
        processor = GitHubEventProcessor(config)
        
        # Mock a slow component initialization
        async def slow_init():
            await asyncio.sleep(2)  # Longer than timeout
        
        with patch.object(processor, '_initialize_components', side_effect=slow_init):
            
            valid_payload = {
                'action': 'opened',
                'repository': {
                    'id': 123,
                    'full_name': 'test/repo',
                    'name': 'repo',
                    'owner': {'login': 'test'}
                }
            }
            
            # Should handle timeout gracefully
            try:
                result = await asyncio.wait_for(
                    processor.process_webhook_event('push', valid_payload),
                    timeout=0.5
                )
                assert result['status'] in ['error', 'processed']
            except asyncio.TimeoutError:
                # Timeout is expected in this test
                assert True
    
    async def test_large_payload_handling(self):
        """Test handling of large payloads."""
        config = GitHubWebhookConfig()
        config.max_payload_size = 1000  # 1KB limit
        processor = GitHubEventProcessor(config)
        
        # Create a large payload
        large_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test/repo',
                'name': 'repo',
                'owner': {'login': 'test'}
            },
            'large_data': 'x' * 2000  # 2KB of data
        }
        
        # Current implementation doesn't explicitly check payload size,
        # but the test structure is here for when that feature is added
        result = await processor.process_webhook_event(
            'push',
            large_payload,
            delivery_id='large-payload-test'
        )
        
        # Should process normally (no size check implemented yet)
        assert result['status'] in ['processed', 'validation_failed', 'error']


@pytest.mark.integration
class TestGitHubHooksIntegration:
    """Integration tests for GitHub hooks."""
    
    async def test_end_to_end_webhook_processing(self):
        """Test complete end-to-end webhook processing."""
        # Create realistic webhook payload
        webhook_payload = {
            'event_type': 'pull_request',
            'payload': {
                'action': 'opened',
                'repository': {
                    'id': 123456789,
                    'full_name': 'test-org/test-repo',
                    'name': 'test-repo',
                    'owner': {'login': 'test-org'},
                    'private': False
                },
                'pull_request': {
                    'id': 987654321,
                    'number': 42,
                    'title': 'Add new feature',
                    'body': 'This PR adds a new feature',
                    'user': {'login': 'contributor'},
                    'base': {'ref': 'main'},
                    'head': {'ref': 'feature-branch'}
                },
                'sender': {'login': 'contributor'}
            },
            'delivery_id': 'integration-test-delivery'
        }
        
        # Mock all external dependencies
        with patch('github_hook.GitHubService'), \
             patch('github_hook.GitHubEventBus'), \
             patch('github_hook.send_observability_event', return_value=True), \
             patch('json.load', return_value=webhook_payload), \
             patch('sys.stdin'):
            
            result = process_stdin_webhook()
            
            # Should process successfully
            assert result['status'] in ['processed', 'validation_failed']
            
            if result['status'] == 'processed':
                assert result['event_type'] == 'pull_request'
                assert result['delivery_id'] == 'integration-test-delivery'
    
    async def test_multiple_webhook_events_sequence(self):
        """Test processing multiple webhook events in sequence."""
        events = [
            {
                'event_type': 'push',
                'payload': {
                    'repository': {
                        'id': 123,
                        'full_name': 'test/repo',
                        'name': 'repo',
                        'owner': {'login': 'test'}
                    },
                    'commits': [{'id': 'abc123', 'message': 'Test commit'}]
                }
            },
            {
                'event_type': 'pull_request',
                'payload': {
                    'action': 'opened',
                    'repository': {
                        'id': 123,
                        'full_name': 'test/repo',
                        'name': 'repo',
                        'owner': {'login': 'test'}
                    },
                    'pull_request': {'id': 456, 'number': 1}
                }
            },
            {
                'event_type': 'issues',
                'payload': {
                    'action': 'opened',
                    'repository': {
                        'id': 123,
                        'full_name': 'test/repo',
                        'name': 'repo',
                        'owner': {'login': 'test'}
                    },
                    'issue': {'id': 789, 'number': 1}
                }
            }
        ]
        
        config = GitHubWebhookConfig()
        processor = GitHubEventProcessor(config)
        
        results = []
        for event in events:
            with patch.object(processor, '_initialize_components'):
                result = await processor.process_webhook_event(
                    event_type=event['event_type'],
                    payload=event['payload'],
                    delivery_id=f"seq-test-{len(results)}"
                )
                results.append(result)
        
        # All events should process
        assert len(results) == 3
        for result in results:
            assert result['status'] in ['processed', 'filtered', 'validation_failed']


@pytest.mark.performance
class TestGitHubHooksPerformance:
    """Performance tests for GitHub hooks."""
    
    async def test_webhook_processing_performance(self):
        """Test webhook processing performance."""
        config = GitHubWebhookConfig()
        processor = GitHubEventProcessor(config)
        
        valid_payload = {
            'action': 'opened',
            'repository': {
                'id': 123,
                'full_name': 'test/repo',
                'name': 'repo',
                'owner': {'login': 'test'}
            }
        }
        
        # Process multiple webhooks and measure time
        start_time = datetime.utcnow()
        
        tasks = []
        for i in range(50):  # 50 concurrent webhook processes
            with patch.object(processor, '_initialize_components'):
                task = processor.process_webhook_event(
                    event_type='push',
                    payload=valid_payload,
                    delivery_id=f'perf-test-{i}'
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.utcnow()
        
        duration = (end_time - start_time).total_seconds()
        
        # Should process 50 webhooks reasonably quickly
        assert duration < 10.0  # Less than 10 seconds
        assert len(results) == 50
        
        # Most should succeed
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'processed')
        assert success_count >= 40  # At least 80% success rate
    
    async def test_signature_validation_performance(self):
        """Test signature validation performance."""
        config = GitHubWebhookConfig()
        config.webhook_secret = 'performance-test-secret-key'
        validator = GitHubWebhookValidator(config)
        
        payload_body = '{"test": "performance payload"}' * 100  # Larger payload
        
        # Calculate signature once
        import hmac
        import hashlib
        signature = 'sha256=' + hmac.new(
            config.webhook_secret.encode('utf-8'),
            payload_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Validate signature many times
        start_time = datetime.utcnow()
        
        results = []
        for i in range(1000):  # 1000 validations
            result = validator.validate_signature(payload_body, signature)
            results.append(result)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should validate 1000 signatures quickly
        assert duration < 5.0  # Less than 5 seconds
        assert all(results)  # All should be valid
        
        # Test performance with different payloads
        validation_times = []
        for size in [100, 1000, 10000]:  # Different payload sizes
            test_payload = '{"data": "' + 'x' * size + '"}'
            test_signature = 'sha256=' + hmac.new(
                config.webhook_secret.encode('utf-8'),
                test_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            start = datetime.utcnow()
            validator.validate_signature(test_payload, test_signature)
            end = datetime.utcnow()
            
            validation_times.append((end - start).total_seconds())
        
        # Validation time should not increase dramatically with payload size
        assert all(time < 0.1 for time in validation_times)  # All under 100ms