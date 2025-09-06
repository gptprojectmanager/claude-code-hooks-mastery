#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "google-cloud-secret-manager",
# ]
# ///

"""
Auto-Initialize API Keys for Claude Code
========================================

This script automatically initializes and validates API keys for Claude Code sessions.
It can be used as a standalone command or imported as a module.

Usage:
    # Standalone execution
    uv run auto_init_api_keys.py
    
    # As module import (auto-initializes on import)
    import auto_init_api_keys
    
    # Check if initialization was successful
    if auto_init_api_keys.is_initialized():
        print("API keys ready!")
"""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global initialization state
_initialization_state = {
    'attempted': False,
    'successful': False,
    'api_keys_available': False,
    'validation_passed': False,
    'last_error': None
}


def get_claude_env_info() -> Dict[str, str]:
    """Get Claude Code environment information"""
    return {
        'session_id': os.environ.get('CLAUDE_SESSION_ID', 'unknown'),
        'working_directory': os.getcwd(),
        'python_version': sys.version.split()[0],
        'user_home': str(Path.home())
    }


def initialize_api_keys_comprehensive() -> Tuple[bool, Dict]:
    """
    Comprehensive API keys initialization with validation
    
    Returns:
        (success, status_info)
    """
    try:
        # Step 1: Load required modules
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        
        from api_keys_initializer import initialize_api_keys
        from api_keys_validator import APIKeyValidator
        
        logger.info("🔧 Starting comprehensive API keys initialization...")
        
        # Step 2: Initialize API keys
        init_success, init_status = initialize_api_keys(force_refresh=False)
        
        if not init_success:
            logger.error("❌ API keys initialization failed")
            return False, {
                'step': 'initialization',
                'success': False,
                'error': 'Failed to initialize API keys',
                'init_status': init_status
            }
        
        # Step 3: Validate API keys
        validator = APIKeyValidator()
        validation_results = validator.validate_all_keys()
        
        # Check critical keys
        gemini_valid = validation_results.get('GEMINI_API_KEY', {}).get('valid', False)
        
        if not gemini_valid:
            logger.error("❌ GEMINI_API_KEY validation failed")
            return False, {
                'step': 'validation',
                'success': False,
                'error': 'GEMINI_API_KEY validation failed',
                'validation_results': validation_results
            }
        
        # Step 4: Success
        valid_keys = sum(1 for result in validation_results.values() if result['valid'])
        total_keys = len(validation_results)
        
        logger.info(f"✅ API keys initialization successful ({valid_keys}/{total_keys} keys valid)")
        
        return True, {
            'step': 'complete',
            'success': True,
            'valid_keys': valid_keys,
            'total_keys': total_keys,
            'validation_results': validation_results,
            'environment': get_claude_env_info()
        }
        
    except ImportError as e:
        logger.error(f"❌ Failed to import required modules: {e}")
        return False, {
            'step': 'import',
            'success': False,
            'error': f'Import error: {e}'
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error during initialization: {e}")
        return False, {
            'step': 'error',
            'success': False,
            'error': f'Unexpected error: {e}'
        }


def check_api_keys_status() -> Dict[str, bool]:
    """Quick check of API keys status in environment"""
    keys_to_check = ['GEMINI_API_KEY', 'GOOGLE_API_KEY',  'FIRECRAWL_API_KEY']
    
    status = {}
    for key in keys_to_check:
        value = os.environ.get(key)
        status[key] = bool(value and len(value.strip()) > 10)
    
    return status


def ensure_gemini_api_key_available() -> Optional[str]:
    """Ensure GEMINI_API_KEY is available and return its value"""
    # Check if already available
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        return gemini_key
    
    # Try initialization if not already attempted successfully
    if not _initialization_state['successful']:
        success, _ = auto_initialize()
        if success:
            return os.environ.get('GEMINI_API_KEY')
    
    return None


def auto_initialize() -> Tuple[bool, Dict]:
    """
    Auto-initialize API keys (called on module import)
    
    Returns:
        (success, status_info)
    """
    global _initialization_state
    
    # Prevent multiple initialization attempts
    if _initialization_state['attempted']:
        return _initialization_state['successful'], {
            'already_attempted': True,
            'previous_success': _initialization_state['successful']
        }
    
    _initialization_state['attempted'] = True
    
    try:
        # Quick check - if GEMINI_API_KEY is already available, consider it successful
        if os.environ.get('GEMINI_API_KEY'):
            logger.info("✅ GEMINI_API_KEY already available, skipping initialization")
            _initialization_state['successful'] = True
            _initialization_state['api_keys_available'] = True
            _initialization_state['validation_passed'] = True
            return True, {'skipped': 'already_available'}
        
        # Perform comprehensive initialization
        success, status_info = initialize_api_keys_comprehensive()
        
        # Update global state
        _initialization_state['successful'] = success
        _initialization_state['api_keys_available'] = success
        _initialization_state['validation_passed'] = success
        
        if not success:
            _initialization_state['last_error'] = status_info.get('error', 'Unknown error')
        
        return success, status_info
        
    except Exception as e:
        error_msg = f"Auto-initialization failed: {e}"
        logger.error(f"❌ {error_msg}")
        _initialization_state['last_error'] = error_msg
        return False, {'error': error_msg}


def is_initialized() -> bool:
    """Check if API keys have been successfully initialized"""
    return _initialization_state['successful']


def get_initialization_status() -> Dict:
    """Get detailed initialization status"""
    return _initialization_state.copy()


def force_reinitialize() -> Tuple[bool, Dict]:
    """Force re-initialization of API keys"""
    global _initialization_state
    
    # Reset state
    _initialization_state['attempted'] = False
    _initialization_state['successful'] = False
    _initialization_state['api_keys_available'] = False
    _initialization_state['validation_passed'] = False
    _initialization_state['last_error'] = None
    
    logger.info("🔄 Forcing API keys re-initialization...")
    return auto_initialize()


def main():
    """Test the auto-initialization system"""
    print("🚀 Auto-Initialize API Keys for Claude Code")
    print("=" * 60)
    
    # Show environment info
    env_info = get_claude_env_info()
    print(f"\n🏠 Environment Info:")
    for key, value in env_info.items():
        print(f"   {key}: {value}")
    
    # Perform initialization
    print(f"\n🔧 Initializing API keys...")
    success, status_info = auto_initialize()
    
    print(f"\n📊 Initialization Result: {'✅ Success' if success else '❌ Failed'}")
    
    if success:
        # Show API keys status
        keys_status = check_api_keys_status()
        print(f"\n🔑 API Keys Status:")
        for key, available in keys_status.items():
            status_icon = "✅" if available else "❌"
            print(f"   {key}: {status_icon}")
        
        # Test GEMINI_API_KEY specifically
        gemini_key = ensure_gemini_api_key_available()
        if gemini_key:
            print(f"\n🎯 GEMINI_API_KEY: Available ({len(gemini_key)} chars)")
        
    else:
        print(f"\n❌ Error: {status_info.get('error', 'Unknown error')}")
    
    # Show final status
    final_status = get_initialization_status()
    print(f"\n📋 Final Status:")
    print(f"   Initialization attempted: {final_status['attempted']}")
    print(f"   Initialization successful: {final_status['successful']}")
    print(f"   API keys available: {final_status['api_keys_available']}")
    print(f"   Validation passed: {final_status['validation_passed']}")
    
    if final_status['last_error']:
        print(f"   Last error: {final_status['last_error']}")
    
    return success


# Auto-initialize on module import (unless we're running as main)
if __name__ != "__main__":
    try:
        auto_initialize()
    except Exception as e:
        logger.warning(f"Silent auto-initialization failed: {e}")


if __name__ == "__main__":
    main()