#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "aiohttp",
#     "python-dotenv",
#     "asyncio",
#     "typing-extensions",
# ]
# ///

"""
GitHub Service Core Infrastructure

Provides secure, async GitHub API interactions with rate limiting,
authentication via gh CLI, and comprehensive error handling.
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging

try:
    import aiohttp
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import logging utilities from constants
sys.path.append(str(Path(__file__).parent / "utils"))
try:
    from constants import ensure_session_log_dir, get_session_log_dir
except ImportError:
    def ensure_session_log_dir(session_id: str) -> Path:
        log_dir = Path("logs") / session_id
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def get_session_log_dir(session_id: str) -> Path:
        return Path("logs") / session_id


class GitHubConfig:
    """Configuration for GitHub API service."""
    
    def __init__(self):
        # GitHub API configuration
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.github_api_url = os.getenv('GITHUB_API_URL', 'https://api.github.com')
        self.enabled = os.getenv('GITHUB_SERVICE_ENABLED', 'true').lower() == 'true'
        
        # Rate limiting configuration
        self.rate_limit_requests = int(os.getenv('GITHUB_RATE_LIMIT_REQUESTS', '5000'))
        self.rate_limit_window = int(os.getenv('GITHUB_RATE_LIMIT_WINDOW', '3600'))  # 1 hour
        self.retry_attempts = int(os.getenv('GITHUB_RETRY_ATTEMPTS', '3'))
        self.initial_backoff = float(os.getenv('GITHUB_INITIAL_BACKOFF', '1.0'))
        self.max_backoff = float(os.getenv('GITHUB_MAX_BACKOFF', '60.0'))
        
        # Timeout configuration
        self.timeout = int(os.getenv('GITHUB_TIMEOUT', '30'))
        self.connection_timeout = int(os.getenv('GITHUB_CONNECTION_TIMEOUT', '10'))
        
        # Caching configuration
        self.cache_enabled = os.getenv('GITHUB_CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_ttl = int(os.getenv('GITHUB_CACHE_TTL', '300'))  # 5 minutes
        
        # Session configuration
        self.session_id = os.getenv('CLAUDE_SESSION_ID', 'default-session')


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class GitHubRateLimiter:
    """Rate limiting with exponential backoff for GitHub API."""
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.request_times: List[datetime] = []
        self.rate_limit_reset: Optional[datetime] = None
        self.remaining_requests: Optional[int] = None
    
    async def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        now = datetime.utcnow()
        
        # Remove old requests from sliding window
        cutoff = now - timedelta(seconds=self.config.rate_limit_window)
        self.request_times = [t for t in self.request_times if t > cutoff]
        
        # Check if we're approaching rate limit
        if len(self.request_times) >= self.config.rate_limit_requests * 0.9:  # 90% threshold
            sleep_time = self.config.rate_limit_window / self.config.rate_limit_requests
            await asyncio.sleep(sleep_time)
        
        # Check GitHub's rate limit headers
        if self.rate_limit_reset and now < self.rate_limit_reset:
            if self.remaining_requests is not None and self.remaining_requests <= 1:
                sleep_time = (self.rate_limit_reset - now).total_seconds()
                await asyncio.sleep(min(sleep_time, self.config.max_backoff))
    
    def record_request(self) -> None:
        """Record a request for rate limiting."""
        self.request_times.append(datetime.utcnow())
    
    def update_from_headers(self, headers: Dict[str, str]) -> None:
        """Update rate limit info from response headers."""
        if 'X-RateLimit-Remaining' in headers:
            self.remaining_requests = int(headers['X-RateLimit-Remaining'])
        
        if 'X-RateLimit-Reset' in headers:
            reset_timestamp = int(headers['X-RateLimit-Reset'])
            self.rate_limit_reset = datetime.utcfromtimestamp(reset_timestamp)


class GitHubService:
    """GitHub API service with async operations and comprehensive error handling."""
    
    def __init__(self, config: Optional[GitHubConfig] = None):
        self.config = config or GitHubConfig()
        self.rate_limiter = GitHubRateLimiter(self.config)
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging for the service."""
        log_dir = ensure_session_log_dir(self.config.session_id)
        log_file = log_dir / "github_service.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=self.config.connection_timeout
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': 'Claude-Code-GitHub-Service/1.0'}
            )
    
    async def _close_session(self) -> None:
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_cache_key(self, method: str, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key for request."""
        key_parts = [method, url]
        if params:
            sorted_params = sorted(params.items())
            key_parts.append(str(sorted_params))
        return ':'.join(key_parts)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if valid."""
        if not self.config.cache_enabled or cache_key not in self._cache:
            return None
        
        cached_data = self._cache[cache_key]
        cached_time = datetime.fromisoformat(cached_data['timestamp'])
        
        if datetime.utcnow() - cached_time > timedelta(seconds=self.config.cache_ttl):
            del self._cache[cache_key]
            return None
        
        return cached_data['data']
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save response to cache."""
        if self.config.cache_enabled:
            self._cache[cache_key] = {
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def authenticate_token(self) -> bool:
        """
        Authenticate GitHub token via gh CLI.
        
        Returns:
            bool: True if authenticated successfully, False otherwise
        """
        try:
            self.logger.info("Checking GitHub authentication via gh CLI")
            
            # Check gh CLI authentication status
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info("GitHub authentication successful via gh CLI")
                
                # Get token from gh CLI if not set
                if not self.config.github_token:
                    token_result = subprocess.run(
                        ['gh', 'auth', 'token'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if token_result.returncode == 0:
                        self.config.github_token = token_result.stdout.strip()
                
                return True
            else:
                self.logger.error(f"GitHub authentication failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("GitHub authentication check timed out")
            return False
        except FileNotFoundError:
            self.logger.error("gh CLI not found. Please install GitHub CLI")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            return False
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Make authenticated request to GitHub API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            use_cache: Whether to use caching for GET requests
            
        Returns:
            Dict containing API response data
            
        Raises:
            GitHubAPIError: On API errors or authentication failures
        """
        if not self.config.enabled:
            raise GitHubAPIError("GitHub service is disabled")
        
        url = f"{self.config.github_api_url}/{endpoint.lstrip('/')}"
        
        # Check cache for GET requests
        if method == 'GET' and use_cache:
            cache_key = self._get_cache_key(method, url, params)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for {url}")
                return cached_response
        
        await self._ensure_session()
        
        # Ensure authentication
        if not self.config.github_token:
            auth_success = await self.authenticate_token()
            if not auth_success:
                raise GitHubAPIError("GitHub authentication failed")
        
        headers = {
            'Authorization': f'token {self.config.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Retry logic with exponential backoff
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                # Rate limiting
                await self.rate_limiter.wait_if_needed()
                self.rate_limiter.record_request()
                
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                async with self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                ) as response:
                    
                    # Update rate limit info
                    self.rate_limiter.update_from_headers(dict(response.headers))
                    
                    response_data = await response.json() if response.content_type == 'application/json' else {}
                    
                    if response.status == 200 or response.status == 201:
                        # Cache successful GET requests
                        if method == 'GET' and use_cache:
                            cache_key = self._get_cache_key(method, url, params)
                            self._save_to_cache(cache_key, response_data)
                        
                        self.logger.info(f"Successful {method} request to {endpoint}")
                        return response_data
                    
                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    elif response.status in [401, 403]:  # Authentication error
                        error_msg = f"Authentication failed: {response_data.get('message', 'Unknown error')}"
                        self.logger.error(error_msg)
                        raise GitHubAPIError(error_msg, response.status, response_data)
                    
                    else:
                        error_msg = f"API error: {response_data.get('message', 'Unknown error')}"
                        self.logger.error(f"{error_msg} (status: {response.status})")
                        raise GitHubAPIError(error_msg, response.status, response_data)
            
            except aiohttp.ClientError as e:
                last_exception = e
                backoff_time = min(
                    self.config.initial_backoff * (2 ** attempt),
                    self.config.max_backoff
                )
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {backoff_time}s")
                await asyncio.sleep(backoff_time)
        
        # All retries failed
        error_msg = f"Request failed after {self.config.retry_attempts} attempts"
        if last_exception:
            error_msg += f": {last_exception}"
        
        self.logger.error(error_msg)
        raise GitHubAPIError(error_msg)
    
    async def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dict containing repository information
        """
        self.logger.info(f"Fetching repository info for {owner}/{repo}")
        return await self._make_request('GET', f'repos/{owner}/{repo}')
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = 'main'
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Branch containing changes
            base: Base branch (default: main)
            
        Returns:
            Dict containing created PR information
        """
        self.logger.info(f"Creating pull request in {owner}/{repo}: {title}")
        
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        
        return await self._make_request('POST', f'repos/{owner}/{repo}/pulls', data=data, use_cache=False)
    
    async def manage_issues(self, action: str, owner: str, repo: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage repository issues.
        
        Args:
            action: Action to perform ('create', 'update', 'close', 'list')
            owner: Repository owner
            repo: Repository name
            data: Action-specific data
            
        Returns:
            Dict containing operation result
        """
        self.logger.info(f"Managing issue in {owner}/{repo}: action={action}")
        
        if action == 'list':
            params = data.get('params', {})
            return await self._make_request('GET', f'repos/{owner}/{repo}/issues', params=params)
        
        elif action == 'create':
            issue_data = {
                'title': data['title'],
                'body': data.get('body', ''),
                'assignees': data.get('assignees', []),
                'labels': data.get('labels', [])
            }
            return await self._make_request('POST', f'repos/{owner}/{repo}/issues', data=issue_data, use_cache=False)
        
        elif action == 'update':
            issue_number = data['number']
            update_data = {k: v for k, v in data.items() if k != 'number'}
            return await self._make_request(
                'PATCH', 
                f'repos/{owner}/{repo}/issues/{issue_number}', 
                data=update_data, 
                use_cache=False
            )
        
        elif action == 'close':
            issue_number = data['number']
            close_data = {'state': 'closed'}
            return await self._make_request(
                'PATCH', 
                f'repos/{owner}/{repo}/issues/{issue_number}', 
                data=close_data, 
                use_cache=False
            )
        
        else:
            raise GitHubAPIError(f"Unsupported issue action: {action}")
    
    async def list_workflows(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """
        List repository workflows.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of workflow information
        """
        self.logger.info(f"Listing workflows for {owner}/{repo}")
        
        response = await self._make_request('GET', f'repos/{owner}/{repo}/actions/workflows')
        return response.get('workflows', [])
    
    async def get_workflow_runs(self, owner: str, repo: str, workflow_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Get workflow runs for a specific workflow.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename
            
        Returns:
            List of workflow run information
        """
        self.logger.info(f"Getting workflow runs for {owner}/{repo}/{workflow_id}")
        
        response = await self._make_request('GET', f'repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs')
        return response.get('workflow_runs', [])


def log_github_error(error_data: Dict[str, Any], config: GitHubConfig) -> None:
    """Log GitHub service errors to local file for debugging."""
    
    try:
        log_dir = ensure_session_log_dir(config.session_id)
        error_log_file = log_dir / 'github_service_errors.json'
        
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
        # Fail silently - don't break execution for logging errors
        pass


async def test_github_connection() -> Dict[str, Any]:
    """Test connection to GitHub API."""
    
    config = GitHubConfig()
    
    test_result = {
        'api_url': config.github_api_url,
        'enabled': config.enabled,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if not config.enabled:
        test_result['status'] = 'disabled'
        test_result['message'] = 'GitHub service is disabled via configuration'
        return test_result
    
    try:
        async with GitHubService(config) as github:
            # Test authentication
            auth_success = await github.authenticate_token()
            if not auth_success:
                test_result['status'] = 'auth_failed'
                test_result['message'] = 'GitHub authentication failed'
                return test_result
            
            # Test API access with authenticated user endpoint
            try:
                user_info = await github._make_request('GET', 'user')
                test_result['status'] = 'connected'
                test_result['message'] = f"Successfully connected as {user_info.get('login', 'unknown')}"
                test_result['user_info'] = {
                    'login': user_info.get('login'),
                    'name': user_info.get('name'),
                    'public_repos': user_info.get('public_repos'),
                    'plan': user_info.get('plan', {}).get('name') if user_info.get('plan') else None
                }
            except GitHubAPIError as e:
                test_result['status'] = 'api_error'
                test_result['message'] = f"API error: {e}"
                test_result['status_code'] = e.status_code
                
    except Exception as e:
        test_result['status'] = 'error'
        test_result['message'] = f'Unexpected error: {str(e)}'
        log_github_error({'error': str(e), 'test_type': 'connection_test'}, config)
    
    return test_result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Service Core Infrastructure')
    parser.add_argument('--test', action='store_true', help='Test connection to GitHub API')
    parser.add_argument('--auth', action='store_true', help='Test GitHub authentication')
    parser.add_argument('--repo-info', help='Get repository info (format: owner/repo)')
    parser.add_argument('--list-workflows', help='List workflows for repository (format: owner/repo)')
    
    args = parser.parse_args()
    
    async def main():
        if args.test:
            result = await test_github_connection()
            print(json.dumps(result, indent=2))
        
        elif args.auth:
            config = GitHubConfig()
            async with GitHubService(config) as github:
                success = await github.authenticate_token()
                print(f"Authentication: {'success' if success else 'failed'}")
        
        elif args.repo_info:
            try:
                owner, repo = args.repo_info.split('/')
                config = GitHubConfig()
                async with GitHubService(config) as github:
                    info = await github.get_repo_info(owner, repo)
                    print(json.dumps(info, indent=2))
            except ValueError:
                print("Error: Repository format should be 'owner/repo'")
            except Exception as e:
                print(f"Error: {e}")
        
        elif args.list_workflows:
            try:
                owner, repo = args.list_workflows.split('/')
                config = GitHubConfig()
                async with GitHubService(config) as github:
                    workflows = await github.list_workflows(owner, repo)
                    print(json.dumps(workflows, indent=2))
            except ValueError:
                print("Error: Repository format should be 'owner/repo'")
            except Exception as e:
                print(f"Error: {e}")
        
        else:
            print("Use --test, --auth, --repo-info owner/repo, or --list-workflows owner/repo")
    
    asyncio.run(main())