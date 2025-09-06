"""
Integration Tests for GitHub Service Integration
End-to-end testing of GitHub Service → Event Bus → Primary Controller workflows
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add parent directories to path for imports
test_dir = Path(__file__).parent.parent
if str(test_dir) not in sys.path:
    sys.path.insert(0, str(test_dir))

try:
    from conftest import TestConfig
except ImportError:
    # Fallback if direct import fails
    from tests.github_integration_suite.conftest import TestConfig


class TestGitHubServiceIntegration:
    """Test GitHub Service integration workflows."""
    
    @pytest.mark.integration
    async def test_complete_github_workflow_success(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        test_config: TestConfig,
        github_webhook_payloads
    ):
        """Test complete successful GitHub workflow from webhook to completion."""
        # Setup test data
        webhook_payload = github_webhook_payloads['pull_request']
        expected_events = []
        
        # Mock event publishing to track workflow progress
        async def track_event_publishing(event_type: str, data: Dict[str, Any]) -> str:
            event_id = f"event-{len(expected_events)}"
            expected_events.append({
                'id': event_id,
                'type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
            return event_id
        
        mock_event_bus.publish_event.side_effect = track_event_publishing
        
        # Execute workflow: GitHub Service receives webhook
        async with mock_github_service as github_service:
            # Step 1: Process webhook payload
            webhook_result = await github_service.process_webhook(webhook_payload)
            assert webhook_result['success'] is True
            
            # Verify event bus received webhook event
            mock_event_bus.publish_event.assert_called()
            assert len(expected_events) >= 1
            assert expected_events[0]['type'] == 'github_webhook_received'
            
            # Step 2: Primary controller delegates task
            async with mock_primary_controller as controller:
                delegation_result = await controller.delegate_github_task({
                    'operation': 'pull_request_review',
                    'data': webhook_payload,
                    'source_event_id': expected_events[0]['id']
                })
                
                assert delegation_result['success'] is True
                assert delegation_result['token_id'] is not None
                assert delegation_result['coherence_score'] >= 0.7
                assert delegation_result['operation_time'] < 2.0
                
                # Step 3: Verify cross-component interaction
                # Event bus should have multiple events now
                assert len(expected_events) >= 2
                
                # Step 4: Aggregate results
                aggregation_result = await controller.aggregate_results(
                    delegation_result['token_id']
                )
                
                assert aggregation_result['success'] is True
                assert aggregation_result['saga_id'] is not None
                assert len(aggregation_result['participating_agents']) > 0
    
    @pytest.mark.integration
    async def test_github_error_propagation_and_recovery(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test error propagation through the integration chain and recovery mechanisms."""
        # Setup error scenarios
        github_api_error = {
            'message': 'API rate limit exceeded',
            'status_code': 429,
            'retry_after': 60
        }
        
        # Configure mock to simulate GitHub API error
        mock_github_service.get_repo_info.side_effect = Exception("GitHub API Error")
        
        # Track error events
        error_events = []
        async def track_error_events(event_type: str, data: Dict[str, Any]) -> str:
            if 'error' in event_type.lower():
                error_events.append({
                    'type': event_type,
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat()
                })
            return f"error-event-{len(error_events)}"
        
        mock_event_bus.publish_event.side_effect = track_error_events
        
        # Execute error scenario
        async with mock_github_service as github_service:
            # Attempt operation that will fail
            with pytest.raises(Exception) as exc_info:
                await github_service.get_repo_info("test-owner/test-repo")
            
            assert "GitHub API Error" in str(exc_info.value)
            
            # Verify error event was published
            mock_event_bus.publish_event.assert_called()
            assert len(error_events) >= 1
            
            # Test recovery mechanism through primary controller
            async with mock_primary_controller as controller:
                # Configure controller for error handling
                controller.delegate_github_task.side_effect = None
                controller.delegate_github_task.return_value = {
                    'success': False,
                    'error': 'GitHub service unavailable',
                    'recovery_action': 'retry_with_backoff',
                    'retry_after': 60
                }
                
                # Attempt delegation with error recovery
                recovery_result = await controller.delegate_github_task({
                    'operation': 'repository_analysis',
                    'recovery_mode': True
                })
                
                assert recovery_result['success'] is False
                assert 'error' in recovery_result
                assert 'recovery_action' in recovery_result
    
    @pytest.mark.integration
    async def test_concurrent_github_operations(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        test_config: TestConfig,
        test_data_factory
    ):
        """Test concurrent GitHub operations and resource management."""
        # Create multiple concurrent operations
        operations = [
            test_data_factory.create_operation(
                operation_type="repository_analysis",
                agent_name=f"agent-{i}",
                parameters={'repo': f'test-repo-{i}'}
            ) for i in range(5)
        ]
        
        # Track concurrent executions
        execution_results = []
        start_times = []
        
        async def execute_operation(operation: Dict[str, Any]) -> Dict[str, Any]:
            start_time = datetime.utcnow()
            start_times.append(start_time)
            
            async with mock_primary_controller as controller:
                result = await controller.delegate_github_task(operation)
                
                execution_results.append({
                    'operation': operation,
                    'result': result,
                    'start_time': start_time,
                    'end_time': datetime.utcnow()
                })
                
                return result
        
        # Execute operations concurrently
        concurrent_tasks = [
            execute_operation(op) for op in operations
        ]
        
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # Verify all operations completed
        assert len(execution_results) == 5
        assert len([r for r in results if not isinstance(r, Exception)]) == 5
        
        # Verify concurrency - operations should overlap in time
        time_spans = [
            (result['end_time'] - result['start_time']).total_seconds()
            for result in execution_results
        ]
        
        # All operations should complete reasonably quickly
        assert all(span < 5.0 for span in time_spans)
        
        # Verify resource management - no resource conflicts
        for result in execution_results:
            assert result['result']['success'] is True
    
    @pytest.mark.integration
    async def test_event_bus_github_service_coordination(
        self,
        mock_github_service,
        mock_event_bus,
        test_config: TestConfig
    ):
        """Test coordination between Event Bus and GitHub Service."""
        # Setup event subscription tracking
        subscription_calls = []
        event_publications = []
        
        def track_subscription(event_type: str, handler_func, **kwargs) -> str:
            subscription_calls.append({
                'event_type': event_type,
                'handler': handler_func,
                'kwargs': kwargs,
                'timestamp': datetime.utcnow().isoformat()
            })
            return f"subscription-{len(subscription_calls)}"
        
        async def track_publication(event_type: str, data: Dict[str, Any]) -> str:
            event_publications.append({
                'type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
            return f"publication-{len(event_publications)}"
        
        mock_event_bus.subscribe_handler.side_effect = track_subscription
        mock_event_bus.publish_event.side_effect = track_publication
        
        # Test event subscription setup
        async with mock_github_service as github_service:
            # Simulate GitHub service subscribing to events
            subscription_id = mock_event_bus.subscribe_handler(
                'github_operation_request',
                github_service.handle_operation_request,
                namespace=test_config.krag_test_namespace
            )
            
            assert subscription_id is not None
            assert len(subscription_calls) == 1
            assert subscription_calls[0]['event_type'] == 'github_operation_request'
            
            # Test event publication from GitHub service
            await github_service.notify_operation_complete({
                'operation_id': 'test-op-123',
                'status': 'completed',
                'result': {'data': 'test result'}
            })
            
            # Verify event was published
            mock_event_bus.publish_event.assert_called()
            assert len(event_publications) >= 1
            
            # Test bidirectional communication
            # Event bus should be able to trigger GitHub operations
            operation_request = {
                'operation': 'create_pull_request',
                'parameters': {
                    'title': 'Test PR',
                    'head': 'feature-branch',
                    'base': 'main',
                    'body': 'Test PR description'
                }
            }
            
            # Simulate event bus triggering GitHub operation
            await mock_event_bus.publish_event(
                'github_operation_request',
                operation_request
            )
            
            # Verify coordination works both ways
            assert len(event_publications) >= 2


class TestCrossComponentInteraction:
    """Test interactions across multiple system components."""
    
    @pytest.mark.integration
    async def test_full_system_workflow(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        mock_krag_tools,
        test_config: TestConfig,
        github_webhook_payloads,
        cleanup_test_data
    ):
        """Test complete system workflow from webhook to memory storage."""
        webhook_payload = github_webhook_payloads['issues']
        workflow_events = []
        
        # Track all system interactions
        async def track_workflow_event(component: str, action: str, data: Dict[str, Any]):
            workflow_events.append({
                'component': component,
                'action': action,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Setup tracking for all components
        async def github_webhook_handler(payload):
            await track_workflow_event('github_service', 'webhook_received', payload)
            return {'success': True, 'event_id': 'webhook-123'}
        
        async def event_bus_publisher(event_type, data):
            await track_workflow_event('event_bus', 'event_published', {
                'type': event_type,
                'data': data
            })
            return f"event-{len(workflow_events)}"
        
        async def controller_delegator(task_data):
            await track_workflow_event('primary_controller', 'task_delegated', task_data)
            return {
                'success': True,
                'token_id': 'token-456',
                'agent_name': 'issue-analyzer',
                'coherence_score': 0.9
            }
        
        async def krag_memory_storage(memory_data):
            await track_workflow_event('krag_memory', 'memory_stored', memory_data)
            return True
        
        # Configure mocks with tracking
        mock_github_service.process_webhook.side_effect = github_webhook_handler
        mock_event_bus.publish_event.side_effect = event_bus_publisher
        mock_primary_controller.delegate_github_task.side_effect = controller_delegator
        mock_krag_tools.add_memory.side_effect = krag_memory_storage
        
        # Execute full workflow
        async with mock_github_service as github_service:
            # Step 1: GitHub webhook processing
            webhook_result = await github_service.process_webhook(webhook_payload)
            assert webhook_result['success'] is True
            
            # Step 2: Event bus propagation
            await mock_event_bus.publish_event('github_issue_created', {
                'issue': webhook_payload['issue'],
                'repository': webhook_payload['repository']
            })
            
            # Step 3: Primary controller task delegation
            async with mock_primary_controller as controller:
                delegation_result = await controller.delegate_github_task({
                    'operation': 'issue_analysis',
                    'issue_data': webhook_payload['issue'],
                    'repo_data': webhook_payload['repository']
                })
                
                # Step 4: Memory storage
                await mock_krag_tools.add_memory({
                    'entity_type': 'github_issue',
                    'entity_id': webhook_payload['issue']['id'],
                    'properties': {
                        'title': webhook_payload['issue']['title'],
                        'state': webhook_payload['issue']['state'],
                        'repository': webhook_payload['repository']['full_name']
                    },
                    'namespace': test_config.krag_test_namespace
                })
        
        # Verify complete workflow execution
        assert len(workflow_events) >= 4
        
        # Verify workflow sequence
        components_involved = {event['component'] for event in workflow_events}
        expected_components = {
            'github_service',
            'event_bus', 
            'primary_controller',
            'krag_memory'
        }
        assert components_involved == expected_components
        
        # Verify workflow timing - all events within reasonable timeframe
        timestamps = [datetime.fromisoformat(event['timestamp']) for event in workflow_events]
        total_workflow_time = (timestamps[-1] - timestamps[0]).total_seconds()
        assert total_workflow_time < 5.0  # Workflow should complete quickly
        
        # Add cleanup task
        cleanup_test_data.append(
            lambda: mock_krag_tools.delete_memory({
                'entity_id': webhook_payload['issue']['id'],
                'namespace': test_config.krag_test_namespace
            })
        )
    
    @pytest.mark.integration
    async def test_system_health_check_integration(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test integrated system health check across all components."""
        health_checks = {}
        
        # Collect health status from all components
        async with mock_github_service as github_service:
            github_health = await github_service.health_check()
            health_checks['github_service'] = github_health
            
            async with mock_primary_controller as controller:
                controller_health = await controller.health_check()
                health_checks['primary_controller'] = controller_health
                
                event_bus_health = await mock_event_bus.get_performance_metrics()
                health_checks['event_bus'] = event_bus_health
        
        # Verify all components report healthy status
        assert 'github_service' in health_checks
        assert 'primary_controller' in health_checks
        assert 'event_bus' in health_checks
        
        # Verify health check data structure
        controller_health = health_checks['primary_controller']
        assert 'timestamp' in controller_health
        assert 'session_id' in controller_health
        assert 'overall_status' in controller_health
        assert 'components' in controller_health
        
        # Verify all system components are healthy
        assert controller_health['overall_status'] == 'healthy'
        for component_name, component_health in controller_health['components'].items():
            assert component_health['status'] == 'healthy'


class TestIntegrationErrorScenarios:
    """Test error scenarios in integrated system."""
    
    @pytest.mark.integration
    async def test_cascading_failure_handling(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test handling of cascading failures across system components."""
        # Setup cascading failure scenario
        failure_sequence = []
        
        # GitHub service fails first
        mock_github_service.get_repo_info.side_effect = Exception("GitHub API unavailable")
        
        # Event bus handles the failure
        async def handle_github_failure(event_type, data):
            failure_sequence.append(f"event_bus_handled_{event_type}")
            if event_type == 'github_service_error':
                return 'error-event-123'
            return f"event-{len(failure_sequence)}"
        
        mock_event_bus.publish_event.side_effect = handle_github_failure
        
        # Primary controller implements circuit breaker
        mock_primary_controller.delegate_github_task.side_effect = Exception(
            "Circuit breaker open - GitHub service unavailable"
        )
        
        # Execute failure scenario
        async with mock_github_service as github_service:
            # Initial GitHub failure
            with pytest.raises(Exception) as github_exc:
                await github_service.get_repo_info("test-owner/test-repo")
            
            assert "GitHub API unavailable" in str(github_exc.value)
            
            # Event bus publishes error event
            await mock_event_bus.publish_event('github_service_error', {
                'error': str(github_exc.value),
                'component': 'github_service',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Primary controller circuit breaker triggers
            async with mock_primary_controller as controller:
                with pytest.raises(Exception) as controller_exc:
                    await controller.delegate_github_task({
                        'operation': 'repository_analysis'
                    })
                
                assert "Circuit breaker open" in str(controller_exc.value)
        
        # Verify failure handling sequence
        assert len(failure_sequence) >= 1
        assert any('github_service_error' in event for event in failure_sequence)
    
    @pytest.mark.integration
    async def test_partial_system_recovery(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        test_config: TestConfig
    ):
        """Test system behavior during partial recovery scenarios."""
        recovery_events = []
        
        # Setup partial recovery scenario
        github_recovery_attempts = 0
        
        async def github_partial_recovery(*args, **kwargs):
            nonlocal github_recovery_attempts
            github_recovery_attempts += 1
            
            if github_recovery_attempts <= 2:
                recovery_events.append(f"github_attempt_{github_recovery_attempts}_failed")
                raise Exception(f"GitHub still recovering (attempt {github_recovery_attempts})")
            else:
                recovery_events.append(f"github_attempt_{github_recovery_attempts}_success")
                return {'success': True, 'status': 'recovered'}
        
        mock_github_service.health_check.side_effect = github_partial_recovery
        
        # Test recovery process
        for attempt in range(4):
            try:
                async with mock_github_service as github_service:
                    health_result = await github_service.health_check()
                    if health_result['success']:
                        recovery_events.append("system_fully_recovered")
                        break
            except Exception as e:
                recovery_events.append(f"recovery_attempt_{attempt + 1}_failed")
                await asyncio.sleep(0.1)  # Brief delay between attempts
        
        # Verify recovery sequence
        assert len(recovery_events) >= 3
        assert recovery_events[-1] == "system_fully_recovered"
        assert github_recovery_attempts == 3  # Should succeed on third attempt