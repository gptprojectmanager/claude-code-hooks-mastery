"""
Unit Tests for GitHub Service
Comprehensive testing of GitHub API interactions, rate limiting, authentication, and error handling
"""

import pytest
import asyncio
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp

# Import the components to test
import sys
sys.path.append('/Users/sam/claude-code-hooks-mastery/.claude/hooks')

try:
    from github_service import (
        GitHubService, 
        GitHubConfig, 
        GitHubAPIError, 
        GitHubRateLimiter,
        test_github_connection
    )
except ImportError:
    pytestmark = pytest.mark.skip("GitHub service components not available")


class TestGitHubConfig:
    """Test GitHub configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GitHubConfig()
        
        assert config.github_api_url == 'https://api.github.com'
        assert config.enabled == True
        assert config.rate_limit_requests == 5000
        assert config.rate_limit_window == 3600
        assert config.timeout == 30
        assert config.cache_enabled == True
    
    @patch.dict(os.environ, {
        'GITHUB_TOKEN': 'test-token',
        'GITHUB_API_URL': 'https://api.github.example.com',
        'GITHUB_SERVICE_ENABLED': 'false',
        'GITHUB_RATE_LIMIT_REQUESTS': '1000',
        'GITHUB_TIMEOUT': '60'
    })
    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        config = GitHubConfig()
        
        assert config.github_token == 'test-token'
        assert config.github_api_url == 'https://api.github.example.com'
        assert config.enabled == False
        assert config.rate_limit_requests == 1000
        assert config.timeout == 60
    
    def test_session_id_configuration(self):
        """Test session ID configuration."""
        with patch.dict(os.environ, {'CLAUDE_SESSION_ID': 'test-session-123'}):
            config = GitHubConfig()
            assert config.session_id == 'test-session-123'


class TestGitHubRateLimiter:
    """Test GitHub rate limiting functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = GitHubConfig()
        self.config.rate_limit_requests = 10
        self.config.rate_limit_window = 60
        self.rate_limiter = GitHubRateLimiter(self.config)
    
    async def test_rate_limiting_basic(self):
        """Test basic rate limiting functionality."""
        # Should not wait initially
        start_time = datetime.utcnow()
        await self.rate_limiter.wait_if_needed()
        end_time = datetime.utcnow()
        
        assert (end_time - start_time).total_seconds() < 0.1
    
    async def test_rate_limiting_threshold(self):
        """Test rate limiting when approaching threshold."""
        # Fill up the rate limiter
        for _ in range(9):  # 90% of 10 requests
            self.rate_limiter.record_request()
        
        # Should wait when at 90% threshold
        start_time = datetime.utcnow()
        await self.rate_limiter.wait_if_needed()
        end_time = datetime.utcnow()
        
        # Should have waited (more than 1 second due to rate_limit_window/requests)
        assert (end_time - start_time).total_seconds() > 1.0
    
    def test_request_recording(self):
        """Test request recording functionality."""
        initial_count = len(self.rate_limiter.request_times)
        
        self.rate_limiter.record_request()
        assert len(self.rate_limiter.request_times) == initial_count + 1
        
        # Verify timestamp is recent
        last_request_time = self.rate_limiter.request_times[-1]
        time_diff = (datetime.utcnow() - last_request_time).total_seconds()
        assert time_diff < 1.0  # Less than 1 second ago
    
    def test_headers_update(self):
        """Test updating rate limit info from headers."""
        headers = {
            'X-RateLimit-Remaining': '100',
            'X-RateLimit-Reset': str(int((datetime.utcnow() + timedelta(minutes=30)).timestamp()))
        }
        
        self.rate_limiter.update_from_headers(headers)
        
        assert self.rate_limiter.remaining_requests == 100
        assert self.rate_limiter.rate_limit_reset is not None
    
    async def test_github_rate_limit_headers(self):
        """Test handling GitHub rate limit headers."""
        # Set up rate limit reset in the future
        future_time = datetime.utcnow() + timedelta(seconds=10)
        self.rate_limiter.rate_limit_reset = future_time
        self.rate_limiter.remaining_requests = 0
        
        start_time = datetime.utcnow()
        await self.rate_limiter.wait_if_needed()
        end_time = datetime.utcnow()
        
        # Should wait for rate limit reset (but capped at max_backoff)
        wait_time = (end_time - start_time).total_seconds()
        assert wait_time >= 1.0  # Should have waited


class TestGitHubService:
    """Test GitHub Service functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = GitHubConfig()
        self.config.github_token = 'test-token-123'
        self.config.enabled = True
        
    async def test_service_initialization(self):
        """Test service initialization."""
        service = GitHubService(self.config)
        
        assert service.config == self.config
        assert service.rate_limiter is not None
        assert service._session is None  # Not initialized yet
        assert isinstance(service._cache, dict)
    
    async def test_context_manager(self):
        """Test async context manager functionality."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session_class.return_value = mock_session
            
            async with GitHubService(self.config) as service:
                assert service._session is not None
            
            mock_session.close.assert_called_once()
    
    @patch('subprocess.run')
    async def test_authenticate_token_success(self, mock_subprocess):
        """Test successful token authentication via gh CLI."""
        # Mock successful gh auth status
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ''
        
        service = GitHubService(self.config)
        result = await service.authenticate_token()
        
        assert result == True
        mock_subprocess.assert_called()
    
    @patch('subprocess.run')
    async def test_authenticate_token_failure(self, mock_subprocess):
        """Test failed token authentication."""
        # Mock failed gh auth status
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = 'Not authenticated'
        
        service = GitHubService(self.config)
        result = await service.authenticate_token()
        
        assert result == False
    
    @patch('subprocess.run')
    async def test_authenticate_token_timeout(self, mock_subprocess):
        """Test authentication timeout handling."""
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired('gh', 10)
        
        service = GitHubService(self.config)
        result = await service.authenticate_token()
        
        assert result == False
    
    async def test_cache_functionality(self):
        """Test request caching functionality."""
        service = GitHubService(self.config)
        
        # Test cache key generation
        cache_key = service._get_cache_key('GET', '/test', {'param': 'value'})
        assert 'GET' in cache_key
        assert '/test' in cache_key
        assert 'param' in cache_key
        
        # Test cache save/retrieve
        test_data = {'test': 'data'}
        service._save_to_cache(cache_key, test_data)
        
        cached_data = service._get_from_cache(cache_key)
        assert cached_data == test_data
    
    async def test_cache_expiration(self):
        """Test cache TTL expiration."""
        service = GitHubService(self.config)
        service.config.cache_ttl = 1  # 1 second TTL
        
        cache_key = 'test_key'
        test_data = {'test': 'data'}
        
        service._save_to_cache(cache_key, test_data)
        
        # Should get data immediately
        cached_data = service._get_from_cache(cache_key)
        assert cached_data == test_data
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should return None after expiration
        cached_data = service._get_from_cache(cache_key)
        assert cached_data is None
    
    async def test_disabled_service(self):
        """Test behavior when service is disabled."""
        self.config.enabled = False
        service = GitHubService(self.config)
        
        with pytest.raises(GitHubAPIError) as exc_info:
            await service._make_request('GET', '/test')
        
        assert "GitHub service is disabled" in str(exc_info.value)
    
    async def test_make_request_success(self):
        """Test successful API request."""
        mock_response_data = {'test': 'response'}
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_response.content_type = 'application/json'
            mock_response.headers = {}
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session.closed = False
            mock_session_class.return_value = mock_session
            
            service = GitHubService(self.config)
            
            with patch.object(service, 'authenticate_token', return_value=True):
                result = await service._make_request('GET', '/test')
            
            assert result == mock_response_data
    
    async def test_make_request_authentication_error(self):
        """Test API request with authentication error."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.json.return_value = {'message': 'Bad credentials'}
            mock_response.content_type = 'application/json'
            mock_response.headers = {}
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session.closed = False
            mock_session_class.return_value = mock_session
            
            service = GitHubService(self.config)
            
            with patch.object(service, 'authenticate_token', return_value=True):
                with pytest.raises(GitHubAPIError) as exc_info:
                    await service._make_request('GET', '/test')
                
                assert exc_info.value.status_code == 401
                assert 'Authentication failed' in str(exc_info.value)
    
    async def test_make_request_rate_limit(self):
        """Test API request with rate limiting."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {'Retry-After': '1'}
            mock_response.json.return_value = {'message': 'API rate limit exceeded'}
            mock_response.content_type = 'application/json'
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session.closed = False
            mock_session_class.return_value = mock_session
            
            service = GitHubService(self.config)
            service.config.retry_attempts = 1  # Reduce retries for test
            
            with patch.object(service, 'authenticate_token', return_value=True):
                start_time = datetime.utcnow()
                
                with pytest.raises(GitHubAPIError):
                    await service._make_request('GET', '/test')
                
                end_time = datetime.utcnow()
                # Should have waited due to rate limiting
                assert (end_time - start_time).total_seconds() >= 0.5
    
    async def test_retry_logic(self):
        """Test request retry logic with exponential backoff."""
        service = GitHubService(self.config)
        service.config.retry_attempts = 3
        service.config.initial_backoff = 0.1
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session.request.side_effect = aiohttp.ClientError("Connection failed")
            mock_session_class.return_value = mock_session
            
            with patch.object(service, 'authenticate_token', return_value=True):
                start_time = datetime.utcnow()
                
                with pytest.raises(GitHubAPIError) as exc_info:
                    await service._make_request('GET', '/test')
                
                end_time = datetime.utcnow()
                
                # Should have retried multiple times with backoff
                assert 'after 3 attempts' in str(exc_info.value)
                assert (end_time - start_time).total_seconds() >= 0.1  # Some backoff delay
    
    async def test_get_repo_info(self):
        """Test repository information retrieval."""
        mock_repo_data = {
            'id': 123,
            'name': 'test-repo',
            'full_name': 'test-owner/test-repo',
            'private': False,
            'language': 'Python'
        }
        
        service = GitHubService(self.config)
        
        with patch.object(service, '_make_request', return_value=mock_repo_data):
            result = await service.get_repo_info('test-owner', 'test-repo')
            
            assert result == mock_repo_data
            service._make_request.assert_called_once_with('GET', 'repos/test-owner/test-repo')
    
    async def test_create_pull_request(self):
        """Test pull request creation."""
        mock_pr_data = {
            'id': 456,
            'number': 1,
            'title': 'Test PR',
            'url': 'https://github.com/test-owner/test-repo/pull/1',
            'state': 'open'
        }
        
        service = GitHubService(self.config)
        
        with patch.object(service, '_make_request', return_value=mock_pr_data):
            result = await service.create_pull_request(
                'test-owner', 
                'test-repo',
                'Test PR',
                'Test description',
                'feature-branch',
                'main'
            )
            
            assert result == mock_pr_data
            
            # Verify correct API call
            expected_data = {
                'title': 'Test PR',
                'body': 'Test description',
                'head': 'feature-branch',
                'base': 'main'
            }
            service._make_request.assert_called_once_with(
                'POST', 
                'repos/test-owner/test-repo/pulls', 
                data=expected_data, 
                use_cache=False
            )
    
    async def test_manage_issues_list(self):
        """Test issue listing."""
        mock_issues_data = {
            'total_count': 2,
            'items': [
                {'id': 789, 'number': 1, 'title': 'Test Issue 1'},
                {'id': 790, 'number': 2, 'title': 'Test Issue 2'}
            ]
        }
        
        service = GitHubService(self.config)
        
        with patch.object(service, '_make_request', return_value=mock_issues_data):
            result = await service.manage_issues(
                'list', 
                'test-owner', 
                'test-repo', 
                {'params': {'state': 'open'}}
            )
            
            assert result == mock_issues_data
            service._make_request.assert_called_once_with(
                'GET', 
                'repos/test-owner/test-repo/issues', 
                params={'state': 'open'}
            )
    
    async def test_manage_issues_create(self):
        """Test issue creation."""
        mock_issue_data = {'id': 789, 'number': 1, 'title': 'New Issue'}
        
        service = GitHubService(self.config)
        
        with patch.object(service, '_make_request', return_value=mock_issue_data):
            result = await service.manage_issues(
                'create',
                'test-owner',
                'test-repo',
                {
                    'title': 'New Issue',
                    'body': 'Issue description',
                    'labels': ['bug']
                }
            )
            
            assert result == mock_issue_data
            
            expected_data = {
                'title': 'New Issue',
                'body': 'Issue description',
                'assignees': [],
                'labels': ['bug']
            }
            service._make_request.assert_called_once_with(
                'POST',
                'repos/test-owner/test-repo/issues',
                data=expected_data,
                use_cache=False
            )
    
    async def test_list_workflows(self):
        """Test workflow listing."""
        mock_workflows_data = {
            'workflows': [
                {'id': 111, 'name': 'CI', 'path': '.github/workflows/ci.yml'}
            ]
        }
        
        service = GitHubService(self.config)
        
        with patch.object(service, '_make_request', return_value=mock_workflows_data):
            result = await service.list_workflows('test-owner', 'test-repo')
            
            assert result == mock_workflows_data['workflows']
            service._make_request.assert_called_once_with(
                'GET', 
                'repos/test-owner/test-repo/actions/workflows'
            )
    
    async def test_get_workflow_runs(self):
        """Test workflow runs retrieval."""
        mock_runs_data = {
            'workflow_runs': [
                {'id': 222, 'run_number': 1, 'status': 'completed'}
            ]
        }
        
        service = GitHubService(self.config)
        
        with patch.object(service, '_make_request', return_value=mock_runs_data):
            result = await service.get_workflow_runs('test-owner', 'test-repo', 'ci.yml')
            
            assert result == mock_runs_data['workflow_runs']
            service._make_request.assert_called_once_with(
                'GET',
                'repos/test-owner/test-repo/actions/workflows/ci.yml/runs'
            )
    
    async def test_unsupported_issue_action(self):
        """Test handling of unsupported issue actions."""
        service = GitHubService(self.config)
        
        with pytest.raises(GitHubAPIError) as exc_info:
            await service.manage_issues('unsupported_action', 'owner', 'repo', {})
        
        assert 'Unsupported issue action' in str(exc_info.value)


class TestGitHubConnectionTest:
    """Test GitHub connection testing functionality."""
    
    @patch('github_service.GitHubService')
    async def test_connection_test_success(self, mock_service_class):
        """Test successful connection test."""
        mock_service = AsyncMock()
        mock_service.authenticate_token.return_value = True
        mock_service._make_request.return_value = {
            'login': 'test-user',
            'name': 'Test User',
            'public_repos': 10
        }
        
        mock_service_class.return_value = mock_service
        mock_service_class.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = await test_github_connection()
        
        assert result['status'] == 'connected'
        assert 'Successfully connected as test-user' in result['message']
        assert result['user_info']['login'] == 'test-user'
    
    @patch('github_service.GitHubService')
    async def test_connection_test_auth_failure(self, mock_service_class):
        """Test connection test with authentication failure."""
        mock_service = AsyncMock()
        mock_service.authenticate_token.return_value = False
        
        mock_service_class.return_value = mock_service
        mock_service_class.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = await test_github_connection()
        
        assert result['status'] == 'auth_failed'
        assert 'authentication failed' in result['message'].lower()
    
    @patch('github_service.GitHubService')
    async def test_connection_test_disabled(self, mock_service_class):
        """Test connection test when service is disabled."""
        with patch('github_service.GitHubConfig') as mock_config_class:
            mock_config = MagicMock()
            mock_config.enabled = False
            mock_config_class.return_value = mock_config
            
            result = await test_github_connection()
            
            assert result['status'] == 'disabled'
            assert 'disabled' in result['message'].lower()
    
    @patch('github_service.GitHubService')
    async def test_connection_test_api_error(self, mock_service_class):
        """Test connection test with API error."""
        mock_service = AsyncMock()
        mock_service.authenticate_token.return_value = True
        mock_service._make_request.side_effect = GitHubAPIError("API Error", 404)
        
        mock_service_class.return_value = mock_service
        mock_service_class.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = await test_github_connection()
        
        assert result['status'] == 'api_error'
        assert result['status_code'] == 404


@pytest.mark.integration
class TestGitHubServiceIntegration:
    """Integration tests requiring real GitHub API (run with --integration flag)."""
    
    @pytest.mark.skipif(not os.getenv('GITHUB_TOKEN'), reason="Requires GITHUB_TOKEN")
    async def test_real_github_connection(self):
        """Test real GitHub connection (requires token)."""
        config = GitHubConfig()
        
        async with GitHubService(config) as service:
            # Test authentication
            auth_result = await service.authenticate_token()
            assert auth_result == True
            
            # Test API call
            try:
                user_info = await service._make_request('GET', 'user')
                assert 'login' in user_info
                assert 'id' in user_info
            except GitHubAPIError as e:
                pytest.fail(f"Real GitHub API call failed: {e}")


class TestGitHubAPIError:
    """Test GitHub API error handling."""
    
    def test_api_error_creation(self):
        """Test GitHubAPIError creation."""
        error = GitHubAPIError("Test error", 404, {"message": "Not found"})
        
        assert str(error) == "Test error"
        assert error.status_code == 404
        assert error.response_data == {"message": "Not found"}
    
    def test_api_error_defaults(self):
        """Test GitHubAPIError with default values."""
        error = GitHubAPIError("Test error")
        
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data == {}


@pytest.mark.performance
class TestGitHubServicePerformance:
    """Performance tests for GitHub Service."""
    
    async def test_concurrent_requests(self):
        """Test concurrent request handling."""
        service = GitHubService(GitHubConfig())
        
        with patch.object(service, '_make_request') as mock_request:
            mock_request.return_value = {'test': 'response'}
            
            # Make 10 concurrent requests
            tasks = [
                service.get_repo_info(f'owner-{i}', f'repo-{i}') 
                for i in range(10)
            ]
            
            start_time = datetime.utcnow()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.utcnow()
            
            # All requests should succeed
            assert len(results) == 10
            assert all(isinstance(r, dict) for r in results)
            
            # Should complete reasonably quickly
            duration = (end_time - start_time).total_seconds()
            assert duration < 5.0  # Should complete within 5 seconds
    
    async def test_rate_limiter_performance(self):
        """Test rate limiter performance under load."""
        config = GitHubConfig()
        config.rate_limit_requests = 100
        rate_limiter = GitHubRateLimiter(config)
        
        start_time = datetime.utcnow()
        
        # Record many requests quickly
        for _ in range(50):
            rate_limiter.record_request()
            await rate_limiter.wait_if_needed()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should handle 50 requests reasonably quickly
        assert duration < 10.0  # Should complete within 10 seconds
        assert len(rate_limiter.request_times) == 50