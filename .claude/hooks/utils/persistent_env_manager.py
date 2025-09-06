#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
# ]
# ///

"""
Persistent Environment Variable Manager
======================================

This utility manages persistent environment variables across Claude Code sessions,
solving the issue where SessionStart hooks cannot set environment variables in 
the parent Claude Code process.
"""

import os
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PersistentEnvManager:
    """Manage persistent environment variables across Claude Code sessions"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the persistent environment manager"""
        self.cache_dir = cache_dir or Path.home() / ".claude" / "env_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "api_keys.json"
        self.lock_file = self.cache_dir / "api_keys.lock"
        
    def save_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """
        Save API keys to persistent cache with timestamp
        
        Args:
            api_keys: Dictionary of environment variable names to values
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "api_keys": api_keys,
                "process_id": os.getpid(),
                "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown")
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"✅ Saved {len(api_keys)} API keys to persistent cache")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save API keys to cache: {e}")
            return False
    
    def load_api_keys(self, max_age_hours: int = 24) -> Dict[str, str]:
        """
        Load API keys from persistent cache if valid
        
        Args:
            max_age_hours: Maximum age of cache in hours before refresh
            
        Returns:
            Dictionary of environment variable names to values
        """
        try:
            if not self.cache_file.exists():
                logger.info("No API keys cache found")
                return {}
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache age
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            age = datetime.now() - cache_time
            
            if age > timedelta(hours=max_age_hours):
                logger.warning(f"API keys cache is {age.total_seconds()/3600:.1f}h old, refreshing...")
                return {}
            
            api_keys = cache_data.get("api_keys", {})
            logger.info(f"✅ Loaded {len(api_keys)} API keys from cache (age: {age.total_seconds()/3600:.1f}h)")
            
            return api_keys
            
        except Exception as e:
            logger.error(f"❌ Failed to load API keys from cache: {e}")
            return {}
    
    def apply_to_environment(self, api_keys: Dict[str, str]) -> int:
        """
        Apply API keys to current environment
        
        Args:
            api_keys: Dictionary of environment variable names to values
            
        Returns:
            Number of environment variables successfully set
        """
        applied_count = 0
        
        for env_var, value in api_keys.items():
            if value:
                os.environ[env_var] = value
                applied_count += 1
                logger.info(f"✅ Set {env_var} in environment")
            else:
                logger.warning(f"⚠️ Skipped empty value for {env_var}")
        
        return applied_count
    
    def refresh_from_secret_manager(self) -> Dict[str, str]:
        """
        Refresh API keys from Google Secret Manager using comprehensive pre_claude_startup.py
        
        Returns:
            Dictionary of refreshed API keys
        """
        try:
            # Import SecureCredentialLoader from pre_claude_startup.py
            script_dir = Path(__file__).parent.parent  # Go up one level to hooks directory
            pre_claude_script = script_dir / "pre_claude_startup.py"
            
            if not pre_claude_script.exists():
                logger.error(f"❌ pre_claude_startup.py not found at {pre_claude_script}")
                return self._fallback_refresh()
            
            # Use the comprehensive SecureCredentialLoader
            sys.path.insert(0, str(script_dir))
            from pre_claude_startup import SecureCredentialLoader
            
            # Initialize the comprehensive loader
            loader = SecureCredentialLoader(project_id="custom-mix-460500-g9")
            
            # Get ALL available credentials using the comprehensive system
            api_keys = loader.get_secure_credentials(force_refresh=True)
            
            if api_keys:
                logger.info(f"🔄 Refreshed {len(api_keys)} API keys from Secret Manager (comprehensive)")
                return api_keys
            else:
                logger.warning("⚠️ No API keys returned from comprehensive loader, trying fallback")
                return self._fallback_refresh()
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh API keys using comprehensive loader: {e}")
            return self._fallback_refresh()
    
    def _fallback_refresh(self) -> Dict[str, str]:
        """
        Fallback refresh method using basic SecretManagerLoader
        
        Returns:
            Dictionary of refreshed API keys
        """
        try:
            # Import SecretManagerLoader for fallback
            script_dir = Path(__file__).parent
            sys.path.insert(0, str(script_dir))
            from secret_manager_loader import SecretManagerLoader
            
            loader = SecretManagerLoader(project_id="custom-mix-460500-g9")
            
            # Get basic API keys as fallback
            api_keys = {}
            
            # Gemini API key (primary)
            gemini_key = loader.get_secret('gemini-api-key', 'GEMINI_API_KEY')
            if gemini_key:
                api_keys['GEMINI_API_KEY'] = gemini_key
                api_keys['GOOGLE_API_KEY'] = gemini_key  # Backward compatibility
            
            # Other API keys
            
            firecrawl_key = loader.get_secret('firecrawl-api-key', 'FIRECRAWL_API_KEY')
            if firecrawl_key:
                api_keys['FIRECRAWL_API_KEY'] = firecrawl_key
            
            openai_key = loader.get_secret('openai-api-key', 'OPENAI_API_KEY')
            if openai_key:
                api_keys['OPENAI_API_KEY'] = openai_key
            
            logger.info(f"🔄 Refreshed {len(api_keys)} API keys from Secret Manager (fallback)")
            return api_keys
            
        except Exception as e:
            logger.error(f"❌ Fallback refresh also failed: {e}")
            return {}
    
    def ensure_api_keys_available(self, force_refresh: bool = False) -> bool:
        """
        Ensure API keys are available in current environment
        
        Args:
            force_refresh: Force refresh from Secret Manager even if cache is valid
            
        Returns:
            True if API keys are available, False otherwise
        """
        try:
            # Check if API keys are already in environment and valid
            if not force_refresh and (os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY')):
                logger.info("✅ API keys already available in environment")
                return True
            
            # Try to load from cache first
            if not force_refresh:
                cached_keys = self.load_api_keys()
                if cached_keys and 'GEMINI_API_KEY' in cached_keys:
                    applied_count = self.apply_to_environment(cached_keys)
                    if applied_count > 0:
                        logger.info(f"✅ Applied {applied_count} API keys from cache")
                        return True
            
            # Refresh from Secret Manager
            fresh_keys = self.refresh_from_secret_manager()
            if fresh_keys and 'GEMINI_API_KEY' in fresh_keys:
                # Save to cache
                self.save_api_keys(fresh_keys)
                
                # Apply to environment
                applied_count = self.apply_to_environment(fresh_keys)
                if applied_count > 0:
                    logger.info(f"✅ Applied {applied_count} fresh API keys")
                    return True
            
            logger.error("❌ No API keys available from any source")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to ensure API keys availability: {e}")
            return False
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Validate that API keys are properly set and accessible
        
        Returns:
            Dictionary mapping API key names to validation status
        """
        validation_results = {}
        
        # Check required API keys
        required_keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY']
        # Include ALL possible API keys from comprehensive loader
        optional_keys = [
             
            'FIRECRAWL_API_KEY',
            'OPENAI_API_KEY',
            'OPENROUTER_API_KEY', 
            'ANTHROPIC_API_KEY'
        ]
        
        for key in required_keys + optional_keys:
            value = os.environ.get(key)
            is_valid = bool(value and len(value.strip()) > 10)  # Basic validation
            validation_results[key] = is_valid
            
            if is_valid:
                logger.info(f"✅ {key}: Valid ({len(value)} chars)")
            else:
                if key in required_keys:
                    logger.warning(f"❌ {key}: Required but invalid or missing")
                else:
                    logger.info(f"ℹ️ {key}: Optional, not provided")
        
        return validation_results


def main():
    """Test the persistent environment manager"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🔧 Testing Persistent Environment Manager")
    print("=" * 50)
    
    manager = PersistentEnvManager()
    
    # Test API key availability
    success = manager.ensure_api_keys_available()
    print(f"\n🔍 API Keys Availability: {'✅ Success' if success else '❌ Failed'}")
    
    # Validate API keys
    validation_results = manager.validate_api_keys()
    print("\n🧪 API Keys Validation:")
    for key, is_valid in validation_results.items():
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"   {key}: {status}")
    
    # Test environment variables
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        print(f"\n✅ GEMINI_API_KEY successfully loaded: {len(gemini_key)} characters")
    else:
        print("\n❌ GEMINI_API_KEY not found in environment")


if __name__ == "__main__":
    main()