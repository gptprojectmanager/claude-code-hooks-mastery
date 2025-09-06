#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
# ]
# ///

"""
API Keys Auto-Initializer
========================

This module automatically loads API keys when imported, providing a seamless
solution for the Claude Code environment variable persistence issue.

Usage:
    import api_keys_initializer  # Automatically loads API keys
    
    # Or explicit initialization
    from api_keys_initializer import initialize_api_keys
    success = initialize_api_keys()
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_persistent_env_manager():
    """Get PersistentEnvManager instance with error handling"""
    try:
        # Import PersistentEnvManager from the same directory
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        from persistent_env_manager import PersistentEnvManager
        return PersistentEnvManager()
    except ImportError as e:
        logger.error(f"Failed to import PersistentEnvManager: {e}")
        return None


def check_api_keys_status() -> Dict[str, bool]:
    """
    Check current status of API keys in environment
    
    Returns:
        Dictionary mapping API key names to availability status
    """
    required_keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY']
    optional_keys = ['FIRECRAWL_API_KEY']
    
    status = {}
    for key in required_keys + optional_keys:
        value = os.environ.get(key)
        status[key] = bool(value and len(value.strip()) > 10)
    
    return status


def initialize_api_keys(force_refresh: bool = False, silent: bool = False) -> Tuple[bool, Dict[str, bool]]:
    """
    Initialize API keys in current environment
    
    Args:
        force_refresh: Force refresh from Secret Manager
        silent: Suppress info logging (keep errors)
        
    Returns:
        Tuple of (success, status_dict)
    """
    if silent:
        logger.setLevel(logging.WARNING)
    
    try:
        # Get manager instance
        manager = get_persistent_env_manager()
        if not manager:
            logger.error("❌ Could not initialize PersistentEnvManager")
            return False, {}
        
        # Ensure API keys are available
        success = manager.ensure_api_keys_available(force_refresh=force_refresh)
        
        # Get final status
        status = check_api_keys_status()
        
        if success and status.get('GEMINI_API_KEY', False):
            if not silent:
                logger.info("✅ API keys successfully initialized")
            return True, status
        else:
            logger.error("❌ API keys initialization failed")
            return False, status
            
    except Exception as e:
        logger.error(f"❌ Exception during API keys initialization: {e}")
        return False, {}


def ensure_gemini_api_key() -> Optional[str]:
    """
    Ensure GEMINI_API_KEY is available and return it
    
    Returns:
        GEMINI_API_KEY value or None if not available
    """
    # Check if already available
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        return gemini_key
    
    # Try to initialize
    success, _ = initialize_api_keys(silent=True)
    if success:
        return os.environ.get('GEMINI_API_KEY')
    
    return None


def test_gemini_api_key() -> bool:
    """
    Test if GEMINI_API_KEY is valid by making a simple API call
    
    Returns:
        True if API key works, False otherwise
    """
    try:
        import requests
        
        api_key = ensure_gemini_api_key()
        if not api_key:
            logger.warning("No GEMINI_API_KEY available for testing")
            return False
        
        # Simple API test - list models
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ GEMINI_API_KEY validation successful")
            return True
        else:
            logger.error(f"❌ GEMINI_API_KEY validation failed: {response.status_code}")
            return False
            
    except ImportError:
        logger.warning("requests module not available for API key testing")
        return False
    except Exception as e:
        logger.error(f"❌ Exception during API key testing: {e}")
        return False


# Auto-initialization when module is imported
_auto_init_attempted = False
_auto_init_success = False

def _auto_initialize():
    """Automatically initialize API keys when module is imported"""
    global _auto_init_attempted, _auto_init_success
    
    if _auto_init_attempted:
        return _auto_init_success
    
    _auto_init_attempted = True
    
    # Only auto-initialize if no GEMINI_API_KEY is present
    if not os.environ.get('GEMINI_API_KEY'):
        try:
            _auto_init_success, _ = initialize_api_keys(silent=True)
        except Exception:
            _auto_init_success = False
    else:
        _auto_init_success = True
    
    return _auto_init_success


# Perform auto-initialization
_auto_initialize()


def main():
    """Test the API keys initializer"""
    print("🚀 Testing API Keys Initializer")
    print("=" * 50)
    
    # Test initialization
    success, status = initialize_api_keys()
    print(f"\n🔧 Initialization Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Show status
    print("\n📊 API Keys Status:")
    for key, available in status.items():
        status_icon = "✅" if available else "❌"
        print(f"   {key}: {status_icon}")
    
    # Test GEMINI_API_KEY specifically
    gemini_key = ensure_gemini_api_key()
    if gemini_key:
        print(f"\n🔑 GEMINI_API_KEY: Available ({len(gemini_key)} chars)")
        
        # Test API key validity
        print("\n🧪 Testing API key validity...")
        is_valid = test_gemini_api_key()
        print(f"   API Key Test: {'✅ Valid' if is_valid else '❌ Invalid'}")
    else:
        print("\n❌ GEMINI_API_KEY: Not available")


if __name__ == "__main__":
    main()