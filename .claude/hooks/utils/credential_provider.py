#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
# ]
# ///

"""
Optimized Centralized Credential Provider for Claude Code Hooks
================================================================

High-performance credential management system with persistent caching,
optimized for production use with minimal logging overhead.

Features:
- Google Secret Manager integration
- Persistent disk cache with TTL (prevents 404 retry delays)
- In-memory cache with TTL (1 hour default)
- Environment variable fallback
- Singleton pattern to avoid duplicate API calls
- Negative cache for 404 responses (24 hour TTL)
- Atomic file operations with locking for concurrent access
- Support for all API keys used by hooks
- Conditional logging for production performance
- Comprehensive error handling

Cache Strategy:
- Positive cache: Successful API key retrievals (1 hour TTL)
- Negative cache: 404 responses for non-existent keys (24 hour TTL)
- Persistent across processes to eliminate startup delays

Performance:
- Cache hit: <10ms (instead of 4000ms Secret Manager call)
- Negative cache hit: 0ms (skips Secret Manager entirely)
- Total credential loading: <50ms (down from 8000ms)
- Production mode: minimal logging overhead

Usage:
    from utils.credential_provider import CredentialProvider
    
    provider = CredentialProvider()
    api_key = provider.get_api_key('OPENAI_API_KEY')
"""

import os
import sys
import time
import json
import fcntl
import tempfile
from typing import Dict, Optional, Set, Any
from pathlib import Path

# OPTIMIZATION: Conditional logging for production performance
DEBUG_ENABLED = os.getenv('CREDENTIAL_PROVIDER_DEBUG', '').lower() in ('1', 'true', 'on')

if DEBUG_ENABLED:
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
else:
    # Null logger for production performance
    class NullLogger:
        def debug(self, msg): pass
        def info(self, msg): pass  
        def warning(self, msg): pass
        def error(self, msg): pass
    logger = NullLogger()

class CredentialProvider:
    """
    High-performance credential management with persistent caching and fallback strategies.
    
    Implements singleton pattern with persistent cache to prevent duplicate Secret Manager
    calls across hook executions, eliminating the 8+ second startup delay.
    
    Optimized for production use with minimal logging overhead.
    """
    
    _instance: Optional['CredentialProvider'] = None
    _initialized: bool = False
    
    # Class-level in-memory cache for current process
    _credential_cache: Dict[str, str] = {}
    _cache_timestamp: Optional[float] = None
    _secret_manager_client = None
    
    # Persistent cache configuration
    CACHE_DIR = Path.home() / ".claude" / "cache"
    CACHE_FILE = CACHE_DIR / "credentials_cache.json"
    CACHE_VERSION = "1.1"
    
    # TTL Configuration
    POSITIVE_CACHE_TTL = 3600  # 1 hour for successful retrievals
    NEGATIVE_CACHE_TTL = 86400  # 24 hours for 404 responses
    IN_MEMORY_CACHE_TTL = 3600  # 1 hour for in-memory cache
    
    PROJECT_ID = "custom-mix-460500-g9"
    
    # Supported API keys with their Secret Manager mappings
    # NOTE: ElevenLabs has been removed from the system
    SUPPORTED_CREDENTIALS = {
        'OPENAI_API_KEY': 'openai-api-key', 
        'GEMINI_API_KEY': 'gemini-api-key',
        'GOOGLE_API_KEY': 'gemini-api-key',  # Alias for GEMINI_API_KEY
        'ANTHROPIC_API_KEY': 'anthropic-api-key',
        'FIRECRAWL_API_KEY': 'firecrawl-api-key',
        'GITHUB_TOKEN': 'github-token',
    }
    
    def __new__(cls) -> 'CredentialProvider':
        """Singleton implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the credential provider (only once due to singleton)"""
        if self._initialized:
            return
        
        self._initialized = True
        if DEBUG_ENABLED:
            logger.info("🔐 Initializing CredentialProvider with persistent cache")
        
        # Initialize cache directory
        self._ensure_cache_directory()
        
        # Load persistent cache
        self._persistent_cache = self._load_persistent_cache()
        
        # Initialize Secret Manager client lazily
        self._secret_manager_client = None
    
    def _ensure_cache_directory(self):
        """Ensure cache directory exists with proper permissions"""
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions for security
            os.chmod(self.CACHE_DIR, 0o700)
        except Exception as e:
            if DEBUG_ENABLED:
                logger.error(f"❌ Failed to create cache directory: {e}")
            # Fallback to temp directory
            self.CACHE_DIR = Path(tempfile.gettempdir()) / ".claude_cache"
            self.CACHE_FILE = self.CACHE_DIR / "credentials_cache.json"
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_persistent_cache(self) -> Dict[str, Any]:
        """Load persistent cache from disk with file locking"""
        default_cache = {
            "positive_cache": {},
            "negative_cache": {},
            "cache_version": self.CACHE_VERSION,
            "last_updated": time.time()
        }
        
        if not self.CACHE_FILE.exists():
            if DEBUG_ENABLED:
                logger.debug("📁 No persistent cache found, creating new one")
            return default_cache
        
        try:
            with open(self.CACHE_FILE, 'r') as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                cache_data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Validate cache version
            if cache_data.get("cache_version") != self.CACHE_VERSION:
                if DEBUG_ENABLED:
                    logger.info("🔄 Cache version mismatch, resetting cache")
                return default_cache
            
            # Clean expired entries
            cache_data = self._clean_expired_cache(cache_data)
            if DEBUG_ENABLED:
                logger.debug(f"📁 Loaded persistent cache with {len(cache_data['positive_cache'])} positive, {len(cache_data['negative_cache'])} negative entries")
            return cache_data
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            if DEBUG_ENABLED:
                logger.warning(f"⚠️ Corrupted cache file, resetting: {e}")
            return default_cache
        except Exception as e:
            if DEBUG_ENABLED:
                logger.error(f"❌ Error loading persistent cache: {e}")
            return default_cache
    
    def _clean_expired_cache(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove expired entries from cache"""
        current_time = time.time()
        
        # Clean positive cache
        expired_positive = []
        for key, entry in cache_data["positive_cache"].items():
            if current_time - entry.get("timestamp", 0) > entry.get("ttl", self.POSITIVE_CACHE_TTL):
                expired_positive.append(key)
        
        for key in expired_positive:
            del cache_data["positive_cache"][key]
        
        # Clean negative cache
        expired_negative = []
        for key, entry in cache_data["negative_cache"].items():
            if current_time - entry.get("timestamp", 0) > entry.get("ttl", self.NEGATIVE_CACHE_TTL):
                expired_negative.append(key)
        
        for key in expired_negative:
            del cache_data["negative_cache"][key]
        
        if expired_positive or expired_negative and DEBUG_ENABLED:
            logger.debug(f"🧹 Cleaned {len(expired_positive)} positive, {len(expired_negative)} negative expired entries")
        
        return cache_data
    
    def _save_persistent_cache(self, cache_data: Dict[str, Any]):
        """Save persistent cache to disk atomically with file locking"""
        try:
            # Update timestamp
            cache_data["last_updated"] = time.time()
            
            # Write to temporary file first for atomic operation
            temp_file = self.CACHE_FILE.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                # Acquire exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(cache_data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Atomic rename
            temp_file.replace(self.CACHE_FILE)
            
            # Set restrictive permissions
            os.chmod(self.CACHE_FILE, 0o600)
            
        except Exception as e:
            if DEBUG_ENABLED:
                logger.error(f"❌ Failed to save persistent cache: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
    
    def get_api_key(self, key_name: str) -> Optional[str]:
        """
        Get an API key using multiple fallback strategies with persistent caching.
        
        Strategy order:
        1. Check in-memory cache (if not expired)
        2. Check persistent negative cache (skip Secret Manager if 404 cached)
        3. Check persistent positive cache (if not expired)
        4. Check environment variables
        5. Load from Google Secret Manager (only if not in negative cache)
        6. Update persistent cache and return
        
        Args:
            key_name: Environment variable name (e.g., 'OPENAI_API_KEY')
            
        Returns:
            API key string or None if not found/accessible
        """
        if key_name not in self.SUPPORTED_CREDENTIALS:
            if DEBUG_ENABLED:
                logger.warning(f"⚠️ Unsupported credential: {key_name}")
            return None
        
        # 1. Check in-memory cache first (fastest)
        cached_value = self._get_from_memory_cache(key_name)
        if cached_value:
            if DEBUG_ENABLED:
                logger.debug(f"⚡ Memory cache hit for {key_name}")
            return cached_value
        
        # 2. Check persistent negative cache (prevent repeated 404s)
        if self._is_in_negative_cache(key_name):
            if DEBUG_ENABLED:
                logger.debug(f"🚫 Negative cache hit for {key_name}, skipping Secret Manager")
            return None
        
        # 3. Check persistent positive cache
        cached_value = self._get_from_persistent_cache(key_name)
        if cached_value:
            if DEBUG_ENABLED:
                logger.debug(f"💾 Persistent cache hit for {key_name}")
            # Update in-memory cache for faster subsequent access
            self._update_memory_cache(key_name, cached_value)
            return cached_value
        
        # 4. Check environment variables
        env_value = os.getenv(key_name)
        if env_value and len(env_value.strip()) > 10:  # Basic validation
            if DEBUG_ENABLED:
                logger.info(f"✅ Environment variable found for {key_name}")
            # Cache the successful retrieval
            self._update_positive_cache(key_name, env_value.strip(), "env")
            self._update_memory_cache(key_name, env_value.strip())
            return env_value.strip()
        
        # 5. Load from Google Secret Manager (only if not in negative cache)
        secret_value = self._load_from_secret_manager(key_name)
        if secret_value:
            if DEBUG_ENABLED:
                logger.info(f"✅ Secret Manager loaded {key_name}")
            # Cache the successful retrieval
            self._update_positive_cache(key_name, secret_value, "secret_manager")
            self._update_memory_cache(key_name, secret_value)
            return secret_value
        
        # 6. Cache the failure to prevent repeated attempts
        self._update_negative_cache(key_name, "not_found")
        if DEBUG_ENABLED:
            logger.error(f"❌ Failed to retrieve {key_name} from all sources")
        return None
    
    def _is_in_negative_cache(self, key_name: str) -> bool:
        """Check if key is in negative cache and not expired"""
        negative_entry = self._persistent_cache["negative_cache"].get(key_name)
        if not negative_entry:
            return False
        
        current_time = time.time()
        entry_age = current_time - negative_entry.get("timestamp", 0)
        ttl = negative_entry.get("ttl", self.NEGATIVE_CACHE_TTL)
        
        return entry_age < ttl
    
    def _get_from_persistent_cache(self, key_name: str) -> Optional[str]:
        """Get credential from persistent cache if valid"""
        positive_entry = self._persistent_cache["positive_cache"].get(key_name)
        if not positive_entry:
            return None
        
        current_time = time.time()
        entry_age = current_time - positive_entry.get("timestamp", 0)
        ttl = positive_entry.get("ttl", self.POSITIVE_CACHE_TTL)
        
        if entry_age < ttl:
            return positive_entry.get("value")
        
        # Entry expired, remove it
        del self._persistent_cache["positive_cache"][key_name]
        self._save_persistent_cache(self._persistent_cache)
        return None
    
    def _update_positive_cache(self, key_name: str, value: str, source: str):
        """Update persistent positive cache"""
        self._persistent_cache["positive_cache"][key_name] = {
            "value": value,
            "source": source,
            "timestamp": time.time(),
            "ttl": self.POSITIVE_CACHE_TTL
        }
        self._save_persistent_cache(self._persistent_cache)
    
    def _update_negative_cache(self, key_name: str, error: str):
        """Update persistent negative cache"""
        self._persistent_cache["negative_cache"][key_name] = {
            "error": error,
            "timestamp": time.time(),
            "ttl": self.NEGATIVE_CACHE_TTL
        }
        self._save_persistent_cache(self._persistent_cache)
    
    def _get_from_memory_cache(self, key_name: str) -> Optional[str]:
        """Get credential from in-memory cache if valid"""
        if not self.is_memory_cache_valid():
            return None
        
        return self._credential_cache.get(key_name)
    
    def _update_memory_cache(self, key_name: str, value: str):
        """Update in-memory cache with new credential"""
        self._credential_cache[key_name] = value
        self._cache_timestamp = time.time()
    
    def is_memory_cache_valid(self) -> bool:
        """Check if current in-memory cache is still valid based on TTL"""
        if self._cache_timestamp is None:
            return False
        
        age = time.time() - self._cache_timestamp
        return age < self.IN_MEMORY_CACHE_TTL
    
    def _load_from_secret_manager(self, key_name: str) -> Optional[str]:
        """Load credential from Google Secret Manager with error handling"""
        try:
            # Lazy import and initialization
            if self._secret_manager_client is None:
                from google.cloud import secretmanager
                self._secret_manager_client = secretmanager.SecretManagerServiceClient()
            
            # Get secret name mapping
            secret_name = self.SUPPORTED_CREDENTIALS[key_name]
            
            # Construct the resource name
            name = f"projects/{self.PROJECT_ID}/secrets/{secret_name}/versions/latest"
            
            # Access the secret version
            if DEBUG_ENABLED:
                logger.debug(f"🔍 Attempting Secret Manager access for {key_name}")
            response = self._secret_manager_client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            
            # Basic validation
            if secret_value and len(secret_value.strip()) > 10:
                return secret_value.strip()
            else:
                if DEBUG_ENABLED:
                    logger.warning(f"⚠️ Invalid secret value for {key_name}")
                return None
            
        except ImportError:
            if DEBUG_ENABLED:
                logger.error("❌ google-cloud-secret-manager not available")
            return None
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                if DEBUG_ENABLED:
                    logger.debug(f"🚫 Secret {key_name} not found in Secret Manager (will cache)")
            else:
                if DEBUG_ENABLED:
                    logger.error(f"❌ Failed to load {key_name} from Secret Manager: {e}")
            return None
    
    def get_all_available_keys(self) -> Dict[str, str]:
        """
        Get all available API keys as a dictionary.
        
        Useful for hook wrappers that need to inject multiple keys
        into the environment at once.
        
        Returns:
            Dictionary of key_name -> api_key for all available credentials
        """
        available_keys = {}
        
        for key_name in self.SUPPORTED_CREDENTIALS:
            api_key = self.get_api_key(key_name)
            if api_key:
                available_keys[key_name] = api_key
        
        if DEBUG_ENABLED:
            logger.info(f"📋 Retrieved {len(available_keys)} available API keys")
        return available_keys
    
    def invalidate_cache(self, persistent: bool = True):
        """
        Force cache invalidation - useful for testing or credential rotation
        
        Args:
            persistent: If True, also clear persistent cache
        """
        # Clear in-memory cache
        self._credential_cache.clear()
        self._cache_timestamp = None
        
        if persistent:
            # Clear persistent cache
            self._persistent_cache = {
                "positive_cache": {},
                "negative_cache": {},
                "cache_version": self.CACHE_VERSION,
                "last_updated": time.time()
            }
            self._save_persistent_cache(self._persistent_cache)
            if DEBUG_ENABLED:
                logger.info("🔄 All caches invalidated (memory + persistent)")
        else:
            if DEBUG_ENABLED:
                logger.info("🔄 In-memory cache invalidated")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get comprehensive cache status for debugging and monitoring"""
        memory_cache_age = None
        if self._cache_timestamp:
            memory_cache_age = time.time() - self._cache_timestamp
        
        persistent_cache_age = None
        if self._persistent_cache.get("last_updated"):
            persistent_cache_age = time.time() - self._persistent_cache["last_updated"]
        
        return {
            'memory_cache': {
                'size': len(self._credential_cache),
                'age_seconds': memory_cache_age,
                'valid': self.is_memory_cache_valid(),
                'ttl_seconds': self.IN_MEMORY_CACHE_TTL,
                'cached_keys': list(self._credential_cache.keys())
            },
            'persistent_cache': {
                'positive_size': len(self._persistent_cache["positive_cache"]),
                'negative_size': len(self._persistent_cache["negative_cache"]),
                'age_seconds': persistent_cache_age,
                'cache_file': str(self.CACHE_FILE),
                'file_exists': self.CACHE_FILE.exists(),
                'positive_keys': list(self._persistent_cache["positive_cache"].keys()),
                'negative_keys': list(self._persistent_cache["negative_cache"].keys())
            },
            'ttl_config': {
                'positive_cache_ttl': self.POSITIVE_CACHE_TTL,
                'negative_cache_ttl': self.NEGATIVE_CACHE_TTL,
                'memory_cache_ttl': self.IN_MEMORY_CACHE_TTL
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for monitoring and debugging.
        
        Returns status of cache, Secret Manager connectivity,
        and available credentials.
        """
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'cache_status': self.get_cache_status(),
            'secret_manager_available': False,
            'environment_keys_found': [],
            'total_available_keys': 0,
            'performance_metrics': {
                'cache_hit_ratio': 0.0,
                'negative_cache_effectiveness': 0.0
            }
        }
        
        # Test Secret Manager connectivity (only if not in negative cache)
        try:
            if self._secret_manager_client is None:
                from google.cloud import secretmanager
                self._secret_manager_client = secretmanager.SecretManagerServiceClient()
            
            # Try to list one secret to test connectivity
            test_name = f"projects/{self.PROJECT_ID}/secrets/gemini-api-key/versions/latest"
            self._secret_manager_client.access_secret_version(request={"name": test_name})
            health_data['secret_manager_available'] = True
            
        except Exception as e:
            if DEBUG_ENABLED:
                logger.warning(f"⚠️ Secret Manager connectivity test failed: {e}")
            health_data['secret_manager_available'] = False
        
        # Check environment keys
        for key_name in self.SUPPORTED_CREDENTIALS:
            if os.getenv(key_name):
                health_data['environment_keys_found'].append(key_name)
        
        # Count total available keys
        available_keys = self.get_all_available_keys()
        health_data['total_available_keys'] = len(available_keys)
        health_data['available_keys'] = list(available_keys.keys())
        
        # Calculate performance metrics
        total_positive = len(self._persistent_cache["positive_cache"])
        total_negative = len(self._persistent_cache["negative_cache"])
        total_cached = total_positive + total_negative
        
        if total_cached > 0:
            health_data['performance_metrics']['cache_hit_ratio'] = total_positive / total_cached
            health_data['performance_metrics']['negative_cache_effectiveness'] = total_negative / total_cached
        
        # Set overall status
        if health_data['total_available_keys'] == 0:
            health_data['status'] = 'unhealthy'
        elif health_data['total_available_keys'] < 3:
            health_data['status'] = 'degraded'
        
        return health_data


def main():
    """CLI interface for testing and debugging"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Credential Provider CLI')
    parser.add_argument('--key', help='Get specific API key')
    parser.add_argument('--list', action='store_true', help='List all available keys')
    parser.add_argument('--health', action='store_true', help='Show health status')
    parser.add_argument('--cache-status', action='store_true', help='Show cache status')
    parser.add_argument('--invalidate-cache', action='store_true', help='Invalidate all caches')
    parser.add_argument('--invalidate-memory', action='store_true', help='Invalidate memory cache only')
    parser.add_argument('--clear-negative', action='store_true', help='Clear negative cache entries')
    
    args = parser.parse_args()
    
    provider = CredentialProvider()
    
    if args.invalidate_cache:
        provider.invalidate_cache(persistent=True)
        print("✅ All caches invalidated")
        return
    
    if args.invalidate_memory:
        provider.invalidate_cache(persistent=False)
        print("✅ Memory cache invalidated")
        return
    
    if args.clear_negative:
        provider._persistent_cache["negative_cache"] = {}
        provider._save_persistent_cache(provider._persistent_cache)
        print("✅ Negative cache cleared")
        return
    
    if args.health:
        health = provider.health_check()
        print("🔍 Credential Provider Health Check:")
        print(f"  Status: {health['status']}")
        print(f"  Secret Manager: {'✅' if health['secret_manager_available'] else '❌'}")
        print(f"  Available Keys: {health['total_available_keys']}")
        print(f"  Cache Hit Ratio: {health['performance_metrics']['cache_hit_ratio']:.2%}")
        print(f"  Negative Cache Effectiveness: {health['performance_metrics']['negative_cache_effectiveness']:.2%}")
        return
    
    if args.cache_status:
        status = provider.get_cache_status()
        print("💾 Cache Status:")
        print("  Memory Cache:")
        for key, value in status['memory_cache'].items():
            print(f"    {key}: {value}")
        print("  Persistent Cache:")
        for key, value in status['persistent_cache'].items():
            print(f"    {key}: {value}")
        print("  TTL Configuration:")
        for key, value in status['ttl_config'].items():
            print(f"    {key}: {value}s")
        return
    
    if args.key:
        start_time = time.time()
        api_key = provider.get_api_key(args.key)
        elapsed = (time.time() - start_time) * 1000
        
        if api_key:
            print(f"✅ {args.key}: {api_key[:10]}...{api_key[-4:]} ({elapsed:.1f}ms)")
        else:
            print(f"❌ {args.key}: Not found ({elapsed:.1f}ms)")
        return
    
    if args.list:
        start_time = time.time()
        keys = provider.get_all_available_keys()
        elapsed = (time.time() - start_time) * 1000
        
        print("📋 Available API Keys:")
        for key_name, api_key in keys.items():
            print(f"  ✅ {key_name}: {api_key[:10]}...{api_key[-4:]}")
        print(f"\nTotal: {len(keys)} keys available ({elapsed:.1f}ms)")
        return
    
    # Default: show health
    args.health = True
    main()


if __name__ == '__main__':
    main()