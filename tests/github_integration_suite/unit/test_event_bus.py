"""
Unit Tests for GitHub Event Bus
Comprehensive testing of event publishing, subscription, namespace isolation, and performance
"""

import pytest
import asyncio
import json
import re
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Import the components to test
import sys
sys.path.append('/Users/sam/claude-code-hooks-mastery/.claude/hooks')

try:
    from event_bus import (
        GitHubEventBus,
        GitHubEvent, 
        EventMetadata,
        EventSubscription,
        EventType,
        get_event_bus,
        test_event_bus
    )
except ImportError:
    pytestmark = pytest.mark.skip("Event bus components not available")


class TestEventType:
    """Test event type enumeration."""
    
    def test_event_type_values(self):
        """Test event type enum values."""
        assert EventType.GITHUB_PR_CREATED.value == "github.pr.created"
        assert EventType.GITHUB_PR_UPDATED.value == "github.pr.updated"
        assert EventType.AGENT_TASK_STARTED.value == "agent.task.started"
        assert EventType.SYSTEM_ERROR.value == "system.error"
    
    def test_all_event_types_available(self):
        """Test that all expected event types are available."""
        expected_types = [
            'GITHUB_PR_CREATED', 'GITHUB_PR_UPDATED', 
            'GITHUB_ISSUE_CREATED', 'GITHUB_ISSUE_UPDATED',
            'GITHUB_WORKFLOW_STARTED', 'GITHUB_WORKFLOW_COMPLETED',
            'AGENT_TASK_STARTED', 'AGENT_TASK_COMPLETED',
            'AGENT_HANDOFF_REQUESTED', 'AGENT_HANDOFF_COMPLETED',
            'SYSTEM_ERROR', 'SYSTEM_WARNING'
        ]
        
        for event_type in expected_types:
            assert hasattr(EventType, event_type)


class TestEventMetadata:
    """Test event metadata structure."""
    
    def test_metadata_creation(self):
        """Test event metadata creation."""
        metadata = EventMetadata(
            event_id="test-123",
            timestamp="2023-01-01T00:00:00Z",
            source_agent="test-agent",
            target_agents=["agent1", "agent2"],
            correlation_id="corr-123",
            retry_count=1,
            namespace="test-namespace"
        )
        
        assert metadata.event_id == "test-123"
        assert metadata.source_agent == "test-agent"
        assert metadata.target_agents == ["agent1", "agent2"]
        assert metadata.correlation_id == "corr-123"
        assert metadata.retry_count == 1
        assert metadata.namespace == "test-namespace"
    
    def test_metadata_defaults(self):
        """Test event metadata with default values."""
        metadata = EventMetadata(
            event_id="test-123",
            timestamp="2023-01-01T00:00:00Z",
            source_agent="test-agent",
            target_agents=[]
        )
        
        assert metadata.correlation_id is None
        assert metadata.retry_count == 0
        assert metadata.namespace == "default"


class TestGitHubEvent:
    """Test GitHub event structure."""
    
    def setup_method(self):
        """Setup test event."""
        self.metadata = EventMetadata(
            event_id="test-123",
            timestamp="2023-01-01T00:00:00Z",
            source_agent="test-agent",
            target_agents=["target-agent"],
            namespace="test"
        )
        
        self.event = GitHubEvent(
            event_type="test.event",
            payload={"test": "data"},
            metadata=self.metadata
        )
    
    def test_event_creation(self):
        """Test event creation."""
        assert self.event.event_type == "test.event"
        assert self.event.payload == {"test": "data"}
        assert self.event.metadata.event_id == "test-123"
    
    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        event_dict = self.event.to_dict()
        
        assert event_dict['event_type'] == "test.event"
        assert event_dict['payload'] == {"test": "data"}
        assert 'metadata' in event_dict
        assert 'serialized_at' in event_dict
        assert event_dict['metadata']['event_id'] == "test-123"
    
    def test_event_from_dict(self):
        """Test event deserialization from dictionary."""
        event_dict = self.event.to_dict()
        reconstructed_event = GitHubEvent.from_dict(event_dict)
        
        assert reconstructed_event.event_type == self.event.event_type
        assert reconstructed_event.payload == self.event.payload
        assert reconstructed_event.metadata.event_id == self.event.metadata.event_id
        assert reconstructed_event.metadata.source_agent == self.event.metadata.source_agent


class TestEventSubscription:
    """Test event subscription functionality."""
    
    def test_subscription_creation(self):
        """Test subscription creation."""
        handler = lambda event: None
        subscription = EventSubscription(
            subscription_id="sub-123",
            pattern="github.*",
            handler=handler,
            namespace="test"
        )
        
        assert subscription.subscription_id == "sub-123"
        assert subscription.pattern == "github.*"
        assert subscription.handler == handler
        assert subscription.namespace == "test"
        assert subscription.match_count == 0
    
    def test_subscription_pattern_matching(self):
        """Test subscription pattern matching."""
        handler = lambda event: None
        subscription = EventSubscription("sub-123", "github.*", handler, "test")
        
        # Test matching patterns
        assert subscription.matches("github.pr.created", "test") == True
        assert subscription.matches("github.issue.opened", "test") == True
        
        # Test non-matching patterns
        assert subscription.matches("agent.task.started", "test") == False
        assert subscription.matches("github.pr.created", "other-namespace") == False
    
    def test_subscription_wildcard_namespace(self):
        """Test subscription with wildcard namespace."""
        handler = lambda event: None
        subscription = EventSubscription("sub-123", "github.*", handler, "*")
        
        # Should match any namespace
        assert subscription.matches("github.pr.created", "test") == True
        assert subscription.matches("github.pr.created", "prod") == True
        assert subscription.matches("github.pr.created", "default") == True
    
    def test_subscription_exact_matching(self):
        """Test exact pattern matching."""
        handler = lambda event: None
        subscription = EventSubscription("sub-123", "github.pr.created", handler, "test")
        
        assert subscription.matches("github.pr.created", "test") == True
        assert subscription.matches("github.pr.updated", "test") == False
    
    def test_subscription_invalid_regex(self):
        """Test handling of invalid regex patterns."""
        handler = lambda event: None
        subscription = EventSubscription("sub-123", "[invalid", handler, "test")
        
        # Should fall back to exact matching
        assert subscription.matches("[invalid", "test") == True
        assert subscription.matches("github.pr.created", "test") == False


class TestGitHubEventBus:
    """Test GitHub Event Bus functionality."""
    
    def setup_method(self):
        """Setup test event bus."""
        self.event_bus = GitHubEventBus(
            krag_namespace="test_namespace",
            session_id="test-session"
        )
    
    def test_event_bus_initialization(self):
        """Test event bus initialization."""
        assert self.event_bus.krag_namespace == "test_namespace"
        assert self.event_bus.session_id == "test-session"
        assert isinstance(self.event_bus.subscriptions, dict)
        assert isinstance(self.event_bus.event_history, list)
        assert isinstance(self.event_bus.performance_metrics, dict)
    
    def test_event_bus_configuration(self):
        """Test event bus configuration from environment."""
        with patch.dict('os.environ', {
            'EVENT_BUS_HISTORY_SIZE': '500',
            'EVENT_BUS_MONITORING': 'false',
            'EVENT_BUS_KRAG_ENABLED': 'false'
        }):
            event_bus = GitHubEventBus()
            
            assert event_bus.max_history_size == 500
            assert event_bus.enable_monitoring == False
            assert event_bus.enable_krag_storage == False
    
    async def test_publish_event_basic(self):
        """Test basic event publishing."""
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            event_id = await self.event_bus.publish_event(
                event_type=EventType.GITHUB_PR_CREATED.value,
                payload={'repo': 'test/repo', 'pr_number': 123},
                agent_context='test-agent'
            )
            
            assert isinstance(event_id, str)
            assert len(self.event_bus.event_history) == 1
            assert self.event_bus.performance_metrics['events_published'] == 1
            
            # Check event structure
            event = self.event_bus.event_history[0]
            assert event.event_type == EventType.GITHUB_PR_CREATED.value
            assert event.payload['repo'] == 'test/repo'
            assert event.metadata.source_agent == 'test-agent'
    
    async def test_publish_event_with_targets(self):
        """Test event publishing with target agents."""
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            event_id = await self.event_bus.publish_event(
                event_type=EventType.AGENT_HANDOFF_REQUESTED.value,
                payload={'task': 'analyze_code'},
                agent_context='primary-agent',
                target_agents=['coder', 'reviewer'],
                correlation_id='corr-123'
            )
            
            event = self.event_bus.event_history[0]
            assert event.metadata.target_agents == ['coder', 'reviewer']
            assert event.metadata.correlation_id == 'corr-123'
    
    async def test_publish_event_monitoring(self):
        """Test event publishing with monitoring enabled."""
        self.event_bus.enable_monitoring = True
        
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True), \
             patch.object(self.event_bus, '_send_monitoring_event') as mock_monitoring:
            
            await self.event_bus.publish_event(
                event_type=EventType.SYSTEM_ERROR.value,
                payload={'error': 'test error'},
                agent_context='test-agent'
            )
            
            mock_monitoring.assert_called_once()
            call_args = mock_monitoring.call_args[0]
            assert call_args[0] == 'EventPublished'
            assert 'event_id' in call_args[1]
    
    async def test_subscribe_handler(self):
        """Test handler subscription."""
        events_received = []
        
        async def test_handler(event_data):
            events_received.append(event_data)
        
        subscription_id = await self.event_bus.subscribe_handler(
            event_pattern="github.*",
            handler_func=test_handler,
            namespace="test_namespace"
        )
        
        assert isinstance(subscription_id, str)
        assert subscription_id in self.event_bus.subscriptions
        assert self.event_bus.performance_metrics['subscriptions_active'] == 1
        
        # Test subscription properties
        subscription = self.event_bus.subscriptions[subscription_id]
        assert subscription.pattern == "github.*"
        assert subscription.namespace == "test_namespace"
    
    async def test_subscription_monitoring(self):
        """Test subscription with monitoring enabled."""
        self.event_bus.enable_monitoring = True
        
        with patch.object(self.event_bus, '_send_monitoring_event') as mock_monitoring:
            subscription_id = await self.event_bus.subscribe_handler(
                event_pattern="github.*",
                handler_func=lambda event: None
            )
            
            mock_monitoring.assert_called_once()
            call_args = mock_monitoring.call_args[0]
            assert call_args[0] == 'HandlerSubscribed'
            assert call_args[1]['subscription_id'] == subscription_id
    
    async def test_unsubscribe_handler(self):
        """Test handler unsubscription."""
        # Subscribe first
        subscription_id = await self.event_bus.subscribe_handler(
            event_pattern="test.*",
            handler_func=lambda event: None
        )
        
        assert len(self.event_bus.subscriptions) == 1
        
        # Unsubscribe
        result = await self.event_bus.unsubscribe_handler(subscription_id)
        
        assert result == True
        assert len(self.event_bus.subscriptions) == 0
        assert self.event_bus.performance_metrics['subscriptions_active'] == 0
    
    async def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing non-existent handler."""
        result = await self.event_bus.unsubscribe_handler("non-existent-id")
        
        assert result == False
    
    async def test_event_processing_async_handler(self):
        """Test event processing with async handler."""
        events_received = []
        
        async def async_handler(event_data):
            events_received.append(event_data)
        
        # Subscribe handler
        subscription_id = await self.event_bus.subscribe_handler(
            event_pattern="github.*",
            handler_func=async_handler,
            namespace="test_namespace"
        )
        
        # Publish event
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            await self.event_bus.publish_event(
                event_type=EventType.GITHUB_PR_CREATED.value,
                payload={'test': 'data'},
                agent_context='test-agent'
            )
        
        # Allow event processing
        await asyncio.sleep(0.1)
        
        assert len(events_received) == 1
        assert events_received[0]['event_type'] == EventType.GITHUB_PR_CREATED.value
        assert self.event_bus.performance_metrics['events_processed'] == 1
    
    async def test_event_processing_sync_handler(self):
        """Test event processing with synchronous handler."""
        events_received = []
        
        def sync_handler(event_data):
            events_received.append(event_data)
        
        # Subscribe handler
        await self.event_bus.subscribe_handler(
            event_pattern="system.*",
            handler_func=sync_handler,
            namespace="test_namespace"
        )
        
        # Publish event
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            await self.event_bus.publish_event(
                event_type=EventType.SYSTEM_WARNING.value,
                payload={'warning': 'test warning'},
                agent_context='test-agent'
            )
        
        # Allow event processing
        await asyncio.sleep(0.1)
        
        assert len(events_received) == 1
        assert events_received[0]['event_type'] == EventType.SYSTEM_WARNING.value
    
    async def test_multiple_handlers_same_pattern(self):
        """Test multiple handlers for the same pattern."""
        handler1_events = []
        handler2_events = []
        
        async def handler1(event_data):
            handler1_events.append(event_data)
        
        async def handler2(event_data):
            handler2_events.append(event_data)
        
        # Subscribe both handlers
        await self.event_bus.subscribe_handler("github.*", handler1, "test_namespace")
        await self.event_bus.subscribe_handler("github.*", handler2, "test_namespace")
        
        # Publish event
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            await self.event_bus.publish_event(
                event_type=EventType.GITHUB_ISSUE_CREATED.value,
                payload={'issue': 'test issue'},
                agent_context='test-agent'
            )
        
        # Allow processing
        await asyncio.sleep(0.1)
        
        # Both handlers should receive the event
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1
        assert self.event_bus.performance_metrics['events_processed'] == 2
    
    async def test_handler_error_handling(self):
        """Test error handling in event handlers."""
        def failing_handler(event_data):
            raise ValueError("Handler error")
        
        await self.event_bus.subscribe_handler("github.*", failing_handler, "test_namespace")
        
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            await self.event_bus.publish_event(
                event_type=EventType.GITHUB_PR_CREATED.value,
                payload={'test': 'data'},
                agent_context='test-agent'
            )
        
        # Allow processing
        await asyncio.sleep(0.1)
        
        # Error should be tracked but not crash the system
        assert self.event_bus.performance_metrics['errors_count'] == 1
    
    async def test_namespace_isolation(self):
        """Test event namespace isolation."""
        ns1_events = []
        ns2_events = []
        
        async def ns1_handler(event_data):
            ns1_events.append(event_data)
        
        async def ns2_handler(event_data):
            ns2_events.append(event_data)
        
        # Subscribe to different namespaces
        await self.event_bus.subscribe_handler("github.*", ns1_handler, "namespace1")
        await self.event_bus.subscribe_handler("github.*", ns2_handler, "namespace2")
        
        # Publish to namespace1
        event_bus_ns1 = GitHubEventBus(krag_namespace="namespace1")
        with patch.object(event_bus_ns1, '_store_event_in_krag', return_value=True):
            await event_bus_ns1.publish_event(
                event_type=EventType.GITHUB_PR_CREATED.value,
                payload={'test': 'ns1'},
                agent_context='test-agent'
            )
        
        # Process subscriptions manually for this test
        for event in event_bus_ns1.event_history:
            await self.event_bus._process_subscriptions(event)
        
        await asyncio.sleep(0.1)
        
        # Only namespace1 handler should receive the event
        assert len(ns1_events) == 1
        assert len(ns2_events) == 0
    
    async def test_get_event_history(self):
        """Test event history retrieval."""
        # Publish multiple events
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            for i in range(5):
                await self.event_bus.publish_event(
                    event_type=EventType.GITHUB_PR_CREATED.value,
                    payload={'pr_number': i},
                    agent_context=f'agent-{i}'
                )
        
        # Get full history
        history = await self.event_bus.get_event_history()
        assert len(history) == 5
        
        # Get limited history
        limited_history = await self.event_bus.get_event_history(limit=3)
        assert len(limited_history) == 3
    
    async def test_get_event_history_with_filters(self):
        """Test event history with namespace and type filters."""
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            await self.event_bus.publish_event(
                event_type=EventType.GITHUB_PR_CREATED.value,
                payload={'test': 1},
                agent_context='test-agent'
            )
            
            await self.event_bus.publish_event(
                event_type=EventType.SYSTEM_ERROR.value,
                payload={'test': 2},
                agent_context='test-agent'
            )
        
        # Filter by event type
        github_events = await self.event_bus.get_event_history(event_type_filter="github.*")
        assert len(github_events) == 1
        assert github_events[0]['event_type'] == EventType.GITHUB_PR_CREATED.value
        
        system_events = await self.event_bus.get_event_history(event_type_filter="system.*")
        assert len(system_events) == 1
        assert system_events[0]['event_type'] == EventType.SYSTEM_ERROR.value
    
    async def test_performance_metrics(self):
        """Test performance metrics tracking."""
        initial_metrics = self.event_bus.get_performance_metrics()
        
        # Publish events and subscribe handlers
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            await self.event_bus.subscribe_handler("github.*", lambda e: None)
            
            for i in range(3):
                await self.event_bus.publish_event(
                    event_type=EventType.GITHUB_PR_CREATED.value,
                    payload={'test': i},
                    agent_context='test-agent'
                )
        
        await asyncio.sleep(0.1)  # Allow processing
        
        metrics = self.event_bus.get_performance_metrics()
        
        assert metrics['events_published'] == initial_metrics['events_published'] + 3
        assert metrics['active_subscriptions'] == 1
        assert metrics['history_size'] >= 3
    
    async def test_clear_history(self):
        """Test clearing event history."""
        # Add some events
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            await self.event_bus.publish_event(
                event_type=EventType.GITHUB_PR_CREATED.value,
                payload={'test': 'data'},
                agent_context='test-agent'
            )
        
        assert len(self.event_bus.event_history) == 1
        
        # Clear history
        await self.event_bus.clear_history()
        
        assert len(self.event_bus.event_history) == 0
    
    async def test_history_size_limit(self):
        """Test event history size limiting."""
        self.event_bus.max_history_size = 3
        
        # Publish more events than limit
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            for i in range(5):
                await self.event_bus.publish_event(
                    event_type=EventType.GITHUB_PR_CREATED.value,
                    payload={'pr_number': i},
                    agent_context='test-agent'
                )
        
        # History should be limited
        assert len(self.event_bus.event_history) == 3
        
        # Should contain the most recent events
        pr_numbers = [event.payload['pr_number'] for event in self.event_bus.event_history]
        assert pr_numbers == [2, 3, 4]  # Last 3 events
    
    async def test_replay_events(self):
        """Test event replay functionality."""
        handler_events = []
        
        async def replay_handler(event_data):
            handler_events.append(event_data)
        
        await self.event_bus.subscribe_handler("github.*", replay_handler, "test_namespace")
        
        # Publish events with timestamps
        base_time = datetime.utcnow()
        events_data = []
        
        with patch.object(self.event_bus, '_store_event_in_krag', return_value=True):
            for i in range(3):
                event_id = await self.event_bus.publish_event(
                    event_type=EventType.GITHUB_PR_CREATED.value,
                    payload={'pr_number': i},
                    agent_context='test-agent'
                )
                events_data.append((event_id, i))
        
        # Clear handler events from initial publishing
        handler_events.clear()
        
        # Replay events from start time
        start_time = (base_time - timedelta(minutes=1)).isoformat() + 'Z'
        end_time = (base_time + timedelta(minutes=1)).isoformat() + 'Z'
        
        replayed_count = await self.event_bus.replay_events(start_time, end_time, "github.*")
        
        await asyncio.sleep(0.1)  # Allow processing
        
        assert replayed_count == 3
        assert len(handler_events) == 3
    
    async def test_krag_storage_disabled(self):
        """Test event bus with KRAG storage disabled."""
        self.event_bus.enable_krag_storage = False
        
        # Should still work without KRAG storage
        event_id = await self.event_bus.publish_event(
            event_type=EventType.GITHUB_PR_CREATED.value,
            payload={'test': 'data'},
            agent_context='test-agent'
        )
        
        assert isinstance(event_id, str)
        assert len(self.event_bus.event_history) == 1
    
    @patch('event_bus.send_observability_event')
    async def test_monitoring_event_sending(self, mock_send_event):
        """Test monitoring event sending."""
        mock_send_event.return_value = True
        self.event_bus.enable_monitoring = True
        
        await self.event_bus._send_monitoring_event('TestEvent', {'test': 'payload'})
        
        mock_send_event.assert_called_once_with(
            event_type="EventBus.TestEvent",
            payload={'test': 'payload'},
            session_id=self.event_bus.session_id,
            source_app="github-event-bus"
        )


class TestEventBusGlobalInstance:
    """Test global event bus instance management."""
    
    def test_get_event_bus_singleton(self):
        """Test global event bus singleton behavior."""
        # Clear any existing instance
        import event_bus
        event_bus._event_bus_instance = None
        
        # Get first instance
        bus1 = get_event_bus("test_namespace")
        assert bus1.krag_namespace == "test_namespace"
        
        # Get second instance should be same
        bus2 = get_event_bus("different_namespace")
        assert bus1 is bus2  # Same instance
        assert bus2.krag_namespace == "test_namespace"  # Original namespace preserved


class TestEventBusTestSuite:
    """Test the event bus test suite functionality."""
    
    async def test_event_bus_test_suite(self):
        """Test the complete event bus test suite."""
        result = await test_event_bus()
        
        assert 'timestamp' in result
        assert 'tests' in result
        assert 'overall' in result
        
        # Should have multiple test categories
        expected_tests = ['publish_event', 'subscribe_handler', 'event_processing', 
                         'event_history', 'performance_metrics']
        
        for test_name in expected_tests:
            assert test_name in result['tests']
        
        # Overall status should be calculated
        assert result['overall']['status'] in ['passed', 'partial', 'failed']
        assert 'passed' in result['overall']
        assert 'total' in result['overall']


@pytest.mark.integration
class TestEventBusIntegration:
    """Integration tests for event bus."""
    
    async def test_full_publish_subscribe_cycle(self):
        """Test complete publish-subscribe cycle."""
        event_bus = GitHubEventBus("integration_test")
        
        received_events = []
        
        async def integration_handler(event_data):
            received_events.append(event_data)
        
        # Subscribe handler
        subscription_id = await event_bus.subscribe_handler(
            "integration.*",
            integration_handler,
            "integration_test"
        )
        
        # Publish multiple events
        with patch.object(event_bus, '_store_event_in_krag', return_value=True):
            event_ids = []
            for i in range(5):
                event_id = await event_bus.publish_event(
                    event_type=f"integration.test.{i}",
                    payload={'test_id': i, 'data': f'test_data_{i}'},
                    agent_context='integration-agent',
                    correlation_id=f'corr-{i}'
                )
                event_ids.append(event_id)
        
        # Allow processing
        await asyncio.sleep(0.2)
        
        # Verify all events received
        assert len(received_events) == 5
        
        for i, event_data in enumerate(received_events):
            assert event_data['event_type'] == f"integration.test.{i}"
            assert event_data['payload']['test_id'] == i
            assert event_data['metadata']['correlation_id'] == f'corr-{i}'
        
        # Verify metrics
        metrics = event_bus.get_performance_metrics()
        assert metrics['events_published'] == 5
        assert metrics['events_processed'] == 5
        assert metrics['active_subscriptions'] == 1
        
        # Verify history
        history = await event_bus.get_event_history()
        assert len(history) == 5
        
        # Cleanup
        await event_bus.unsubscribe_handler(subscription_id)
        assert len(event_bus.subscriptions) == 0


@pytest.mark.performance
class TestEventBusPerformance:
    """Performance tests for event bus."""
    
    async def test_high_throughput_publishing(self):
        """Test high-throughput event publishing."""
        event_bus = GitHubEventBus("perf_test")
        
        # Publish many events quickly
        start_time = datetime.utcnow()
        
        with patch.object(event_bus, '_store_event_in_krag', return_value=True):
            tasks = []
            for i in range(100):
                task = event_bus.publish_event(
                    event_type=f"perf.test.{i % 10}",
                    payload={'index': i},
                    agent_context='perf-agent'
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should handle 100 events reasonably quickly
        assert duration < 5.0  # Less than 5 seconds
        assert len(event_bus.event_history) == 100
        assert event_bus.performance_metrics['events_published'] == 100
    
    async def test_many_subscribers_performance(self):
        """Test performance with many subscribers."""
        event_bus = GitHubEventBus("multi_sub_test")
        
        # Create many subscribers
        handlers_count = 50
        received_counts = [0] * handlers_count
        
        def create_handler(index):
            async def handler(event_data):
                received_counts[index] += 1
            return handler
        
        # Subscribe all handlers
        subscription_ids = []
        for i in range(handlers_count):
            subscription_id = await event_bus.subscribe_handler(
                "multi.*",
                create_handler(i),
                "multi_sub_test"
            )
            subscription_ids.append(subscription_id)
        
        # Publish events
        with patch.object(event_bus, '_store_event_in_krag', return_value=True):
            start_time = datetime.utcnow()
            
            for i in range(10):
                await event_bus.publish_event(
                    event_type=f"multi.test.{i}",
                    payload={'index': i},
                    agent_context='multi-agent'
                )
            
            # Allow processing
            await asyncio.sleep(1.0)
            end_time = datetime.utcnow()
        
        duration = (end_time - start_time).total_seconds()
        
        # All handlers should have received all events
        assert all(count == 10 for count in received_counts)
        assert duration < 10.0  # Should complete within 10 seconds
        
        # Cleanup
        for subscription_id in subscription_ids:
            await event_bus.unsubscribe_handler(subscription_id)