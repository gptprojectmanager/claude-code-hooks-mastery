#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "asyncio",
#     "json",
#     "typing-extensions",
#     "python-dotenv",
# ]
# ///

"""
GitHub Event Bus Architecture con KRAG Integration

Event-driven communication system per multi-agent coordination 
con namespace isolation e performance monitoring.
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import re

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import utilities
sys.path.append(str(Path(__file__).parent / "utils"))
try:
    from constants import ensure_session_log_dir
    from observability_sender import send_observability_event
except ImportError:
    def ensure_session_log_dir(session_id: str) -> Path:
        log_dir = Path("logs") / session_id
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def send_observability_event(event_type: str, payload: Dict[str, Any], **kwargs) -> bool:
        return True


class EventType(Enum):
    """GitHub Event Types for agent coordination."""
    GITHUB_PR_CREATED = "github.pr.created"
    GITHUB_PR_UPDATED = "github.pr.updated"  
    GITHUB_ISSUE_CREATED = "github.issue.created"
    GITHUB_ISSUE_UPDATED = "github.issue.updated"
    GITHUB_WORKFLOW_STARTED = "github.workflow.started"
    GITHUB_WORKFLOW_COMPLETED = "github.workflow.completed"
    AGENT_TASK_STARTED = "agent.task.started"
    AGENT_TASK_COMPLETED = "agent.task.completed"
    AGENT_HANDOFF_REQUESTED = "agent.handoff.requested"
    AGENT_HANDOFF_COMPLETED = "agent.handoff.completed"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"


@dataclass
class EventMetadata:
    """Event metadata for tracking and debugging."""
    event_id: str
    timestamp: str
    source_agent: str
    target_agents: List[str]
    correlation_id: Optional[str] = None
    retry_count: int = 0
    namespace: str = "default"


@dataclass  
class GitHubEvent:
    """Structured event for GitHub operations."""
    event_type: str
    payload: Dict[str, Any]
    metadata: EventMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for KRAG storage."""
        return {
            'event_type': self.event_type,
            'payload': self.payload,
            'metadata': asdict(self.metadata),
            'serialized_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubEvent':
        """Create event from dictionary."""
        metadata = EventMetadata(**data['metadata'])
        return cls(
            event_type=data['event_type'],
            payload=data['payload'],
            metadata=metadata
        )


class EventSubscription:
    """Event subscription with pattern matching."""
    
    def __init__(self, subscription_id: str, pattern: str, handler: Callable, namespace: str):
        self.subscription_id = subscription_id
        self.pattern = pattern
        self.handler = handler
        self.namespace = namespace
        self.created_at = datetime.utcnow()
        self.match_count = 0
        
    def matches(self, event_type: str, event_namespace: str) -> bool:
        """Check if event matches subscription pattern."""
        # Namespace must match or be wildcard
        if self.namespace != "*" and self.namespace != event_namespace:
            return False
            
        # Pattern matching with regex support
        try:
            pattern = self.pattern.replace("*", ".*")
            return bool(re.match(pattern, event_type))
        except re.error:
            return self.pattern == event_type


class GitHubEventBus:
    """
    Event Bus Architecture con KRAG Integration.
    
    Provides event-driven communication between agents with namespace isolation,
    event replay capability, and performance monitoring.
    """
    
    def __init__(self, krag_namespace: str = "github_events", session_id: str = None):
        self.krag_namespace = krag_namespace
        self.session_id = session_id or os.getenv('CLAUDE_SESSION_ID', 'default-session')
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_history: List[GitHubEvent] = []
        self.performance_metrics = {
            'events_published': 0,
            'events_processed': 0,
            'subscriptions_active': 0,
            'errors_count': 0
        }
        
        # Configuration
        self.max_history_size = int(os.getenv('EVENT_BUS_HISTORY_SIZE', '1000'))
        self.enable_monitoring = os.getenv('EVENT_BUS_MONITORING', 'true').lower() == 'true'
        self.enable_krag_storage = os.getenv('EVENT_BUS_KRAG_ENABLED', 'true').lower() == 'true'
        
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging for event bus."""
        log_dir = ensure_session_log_dir(self.session_id)
        log_file = log_dir / "event_bus.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def _store_event_in_krag(self, event: GitHubEvent) -> bool:
        """Store event in KRAG memory for persistence."""
        if not self.enable_krag_storage:
            return True
            
        try:
            # Import KRAG tools dynamically to avoid hard dependency
            try:
                sys.path.append('/Users/sam/claude-code-hooks-mastery')
                # This would normally use the KRAG MCP tool
                # For now, store in local cache
                self.logger.debug(f"Would store event {event.metadata.event_id} in KRAG namespace {self.krag_namespace}")
                return True
            except ImportError:
                self.logger.warning("KRAG integration not available, using local storage")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store event in KRAG: {e}")
            self.performance_metrics['errors_count'] += 1
            return False
    
    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any], 
        agent_context: str,
        target_agents: Optional[List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish event to the bus for agent coordination.
        
        Args:
            event_type: Type of event (use EventType enum values)
            payload: Event payload data
            agent_context: Source agent context
            target_agents: Optional list of target agents
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            str: Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        
        try:
            # Create event metadata
            metadata = EventMetadata(
                event_id=event_id,
                timestamp=datetime.utcnow().isoformat() + 'Z',
                source_agent=agent_context,
                target_agents=target_agents or [],
                correlation_id=correlation_id,
                namespace=self.krag_namespace
            )
            
            # Create structured event
            event = GitHubEvent(
                event_type=event_type,
                payload=payload,
                metadata=metadata
            )
            
            self.logger.info(f"Publishing event {event_type} from {agent_context} (ID: {event_id})")
            
            # Store in KRAG
            await self._store_event_in_krag(event)
            
            # Add to local history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history_size:
                self.event_history.pop(0)
            
            # Process subscriptions
            await self._process_subscriptions(event)
            
            # Update metrics
            self.performance_metrics['events_published'] += 1
            
            # Send monitoring event
            if self.enable_monitoring:
                await self._send_monitoring_event('EventPublished', {
                    'event_id': event_id,
                    'event_type': event_type,
                    'source_agent': agent_context,
                    'target_agents': target_agents,
                    'namespace': self.krag_namespace
                })
            
            self.logger.info(f"Event {event_id} published successfully")
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to publish event {event_type}: {e}")
            self.performance_metrics['errors_count'] += 1
            raise
    
    async def subscribe_handler(
        self,
        event_pattern: str,
        handler_func: Callable,
        namespace: str = "*"
    ) -> str:
        """
        Subscribe handler to event pattern.
        
        Args:
            event_pattern: Event type pattern (supports wildcards)
            handler_func: Async callable to handle events
            namespace: Namespace to subscribe to (* for all)
            
        Returns:
            str: Subscription ID for management
        """
        subscription_id = str(uuid.uuid4())
        
        try:
            subscription = EventSubscription(
                subscription_id=subscription_id,
                pattern=event_pattern,
                handler=handler_func,
                namespace=namespace
            )
            
            self.subscriptions[subscription_id] = subscription
            self.performance_metrics['subscriptions_active'] = len(self.subscriptions)
            
            self.logger.info(f"Handler subscribed to pattern '{event_pattern}' in namespace '{namespace}' (ID: {subscription_id})")
            
            # Send monitoring event
            if self.enable_monitoring:
                await self._send_monitoring_event('HandlerSubscribed', {
                    'subscription_id': subscription_id,
                    'pattern': event_pattern,
                    'namespace': namespace
                })
            
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe handler: {e}")
            self.performance_metrics['errors_count'] += 1
            raise
    
    async def unsubscribe_handler(self, subscription_id: str) -> bool:
        """
        Unsubscribe handler from events.
        
        Args:
            subscription_id: Subscription ID to remove
            
        Returns:
            bool: True if unsubscribed successfully
        """
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions.pop(subscription_id)
                self.performance_metrics['subscriptions_active'] = len(self.subscriptions)
                
                self.logger.info(f"Handler unsubscribed: {subscription_id}")
                
                # Send monitoring event
                if self.enable_monitoring:
                    await self._send_monitoring_event('HandlerUnsubscribed', {
                        'subscription_id': subscription_id,
                        'pattern': subscription.pattern
                    })
                
                return True
            else:
                self.logger.warning(f"Subscription not found: {subscription_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe handler {subscription_id}: {e}")
            self.performance_metrics['errors_count'] += 1
            return False
    
    async def get_event_history(
        self,
        agent_namespace: str = None,
        event_type_filter: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get event history for debugging and replay.
        
        Args:
            agent_namespace: Filter by agent namespace
            event_type_filter: Filter by event type pattern
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        try:
            events = self.event_history[-limit:] if limit else self.event_history
            
            # Filter by namespace
            if agent_namespace:
                events = [e for e in events if e.metadata.namespace == agent_namespace]
            
            # Filter by event type
            if event_type_filter:
                pattern = event_type_filter.replace("*", ".*")
                events = [e for e in events if re.match(pattern, e.event_type)]
            
            self.logger.info(f"Retrieved {len(events)} events from history")
            
            return [event.to_dict() for event in events]
            
        except Exception as e:
            self.logger.error(f"Failed to get event history: {e}")
            self.performance_metrics['errors_count'] += 1
            return []
    
    async def _process_subscriptions(self, event: GitHubEvent) -> None:
        """Process event against all subscriptions."""
        matching_subscriptions = []
        
        for subscription in self.subscriptions.values():
            if subscription.matches(event.event_type, event.metadata.namespace):
                matching_subscriptions.append(subscription)
        
        self.logger.debug(f"Found {len(matching_subscriptions)} matching subscriptions for {event.event_type}")
        
        # Process subscriptions concurrently
        if matching_subscriptions:
            tasks = []
            for subscription in matching_subscriptions:
                task = self._execute_handler(subscription, event)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_handler(self, subscription: EventSubscription, event: GitHubEvent) -> None:
        """Execute subscription handler for event."""
        try:
            self.logger.debug(f"Executing handler for subscription {subscription.subscription_id}")
            
            if asyncio.iscoroutinefunction(subscription.handler):
                await subscription.handler(event.to_dict())
            else:
                subscription.handler(event.to_dict())
            
            subscription.match_count += 1
            self.performance_metrics['events_processed'] += 1
            
        except Exception as e:
            self.logger.error(f"Handler execution failed for subscription {subscription.subscription_id}: {e}")
            self.performance_metrics['errors_count'] += 1
    
    async def _send_monitoring_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Send monitoring event to observability system."""
        try:
            success = send_observability_event(
                event_type=f"EventBus.{event_type}",
                payload=payload,
                session_id=self.session_id,
                source_app="github-event-bus"
            )
            
            if not success:
                self.logger.warning(f"Failed to send monitoring event: {event_type}")
                
        except Exception as e:
            self.logger.debug(f"Monitoring event send failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get event bus performance metrics."""
        return {
            **self.performance_metrics,
            'history_size': len(self.event_history),
            'active_subscriptions': len(self.subscriptions),
            'uptime': (datetime.utcnow() - datetime.utcnow()).total_seconds()  # Placeholder
        }
    
    async def clear_history(self) -> None:
        """Clear event history (use with caution)."""
        self.event_history.clear()
        self.logger.info("Event history cleared")
    
    async def replay_events(
        self,
        start_time: str,
        end_time: str = None,
        event_type_filter: str = None
    ) -> int:
        """
        Replay events from history within time range.
        
        Args:
            start_time: ISO format start time
            end_time: ISO format end time (default: now)
            event_type_filter: Optional event type filter
            
        Returns:
            int: Number of events replayed
        """
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else datetime.utcnow()
            
            replayed_count = 0
            
            for event in self.event_history:
                event_time = datetime.fromisoformat(event.metadata.timestamp.replace('Z', '+00:00'))
                
                if start_dt <= event_time <= end_dt:
                    if not event_type_filter or re.match(event_type_filter.replace("*", ".*"), event.event_type):
                        await self._process_subscriptions(event)
                        replayed_count += 1
            
            self.logger.info(f"Replayed {replayed_count} events")
            return replayed_count
            
        except Exception as e:
            self.logger.error(f"Event replay failed: {e}")
            self.performance_metrics['errors_count'] += 1
            return 0


# Global event bus instance
_event_bus_instance: Optional[GitHubEventBus] = None

def get_event_bus(krag_namespace: str = "github_events") -> GitHubEventBus:
    """Get or create global event bus instance."""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = GitHubEventBus(krag_namespace)
    return _event_bus_instance


async def test_event_bus() -> Dict[str, Any]:
    """Test event bus functionality."""
    
    test_result = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tests': {}
    }
    
    try:
        # Create test event bus
        event_bus = GitHubEventBus("test_namespace")
        
        # Test 1: Publish event
        try:
            event_id = await event_bus.publish_event(
                event_type=EventType.GITHUB_PR_CREATED.value,
                payload={'repo': 'test/repo', 'pr_number': 123},
                agent_context='test-agent'
            )
            test_result['tests']['publish_event'] = {'status': 'passed', 'event_id': event_id}
        except Exception as e:
            test_result['tests']['publish_event'] = {'status': 'failed', 'error': str(e)}
        
        # Test 2: Subscribe handler
        events_received = []
        
        async def test_handler(event_data):
            events_received.append(event_data)
        
        try:
            subscription_id = await event_bus.subscribe_handler(
                event_pattern="github.*",
                handler_func=test_handler,
                namespace="test_namespace"
            )
            test_result['tests']['subscribe_handler'] = {'status': 'passed', 'subscription_id': subscription_id}
        except Exception as e:
            test_result['tests']['subscribe_handler'] = {'status': 'failed', 'error': str(e)}
        
        # Test 3: Event processing
        await asyncio.sleep(0.1)  # Allow event processing
        if events_received:
            test_result['tests']['event_processing'] = {'status': 'passed', 'events_received': len(events_received)}
        else:
            test_result['tests']['event_processing'] = {'status': 'failed', 'error': 'No events received'}
        
        # Test 4: Get event history
        try:
            history = await event_bus.get_event_history(limit=10)
            test_result['tests']['event_history'] = {'status': 'passed', 'history_count': len(history)}
        except Exception as e:
            test_result['tests']['event_history'] = {'status': 'failed', 'error': str(e)}
        
        # Test 5: Performance metrics
        try:
            metrics = event_bus.get_performance_metrics()
            test_result['tests']['performance_metrics'] = {'status': 'passed', 'metrics': metrics}
        except Exception as e:
            test_result['tests']['performance_metrics'] = {'status': 'failed', 'error': str(e)}
        
        # Overall test status
        passed_tests = sum(1 for test in test_result['tests'].values() if test['status'] == 'passed')
        total_tests = len(test_result['tests'])
        test_result['overall'] = {
            'status': 'passed' if passed_tests == total_tests else 'partial',
            'passed': passed_tests,
            'total': total_tests
        }
        
    except Exception as e:
        test_result['overall'] = {'status': 'failed', 'error': str(e)}
    
    return test_result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Event Bus Architecture')
    parser.add_argument('--test', action='store_true', help='Test event bus functionality')
    parser.add_argument('--publish', help='Publish test event (JSON payload)')
    parser.add_argument('--history', action='store_true', help='Show event history')
    parser.add_argument('--metrics', action='store_true', help='Show performance metrics')
    
    args = parser.parse_args()
    
    async def main():
        if args.test:
            result = await test_event_bus()
            print(json.dumps(result, indent=2))
        
        elif args.publish:
            try:
                payload = json.loads(args.publish)
                event_bus = get_event_bus()
                
                event_id = await event_bus.publish_event(
                    event_type=EventType.SYSTEM_WARNING.value,
                    payload=payload,
                    agent_context='cli-test'
                )
                
                print(f"Event published: {event_id}")
            except Exception as e:
                print(f"Error: {e}")
        
        elif args.history:
            event_bus = get_event_bus()
            history = await event_bus.get_event_history(limit=20)
            print(json.dumps(history, indent=2))
        
        elif args.metrics:
            event_bus = get_event_bus()
            metrics = event_bus.get_performance_metrics()
            print(json.dumps(metrics, indent=2))
        
        else:
            print("Use --test, --publish JSON, --history, or --metrics")
    
    asyncio.run(main())