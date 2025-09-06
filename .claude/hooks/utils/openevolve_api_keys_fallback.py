#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "google-cloud-secret-manager",
# ]
# ///

"""
OpenEvolve API Keys Fallback System
===================================

Provides emergency API key loading specifically for OpenEvolve workflows.
This is the fallback mechanism when SessionStart hooks fail to provide
persistent environment variables.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OpenEvolveAPIKeysFallback:
    """Emergency API keys loader for OpenEvolve workflows"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent.parent  # Navigate to project root
        
    def emergency_load_gemini_key(self) -> Optional[str]:
        """
        Emergency load of GEMINI_API_KEY using multiple fallback methods
        
        Returns:
            GEMINI_API_KEY value or None if not available
        """
        # Method 1: Check environment
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if gemini_key:
            logger.info("✅ GEMINI_API_KEY found in environment")
            return gemini_key
        
        # Method 2: Try persistent cache
        try:
            gemini_key = self._load_from_persistent_cache()
            if gemini_key:
                os.environ['GEMINI_API_KEY'] = gemini_key
                os.environ['GOOGLE_API_KEY'] = gemini_key  # Backward compatibility
                logger.info("✅ GEMINI_API_KEY loaded from persistent cache")
                return gemini_key
        except Exception as e:
            logger.warning(f"Failed to load from persistent cache: {e}")
        
        # Method 3: Direct Secret Manager access
        try:
            gemini_key = self._load_from_secret_manager()
            if gemini_key:
                os.environ['GEMINI_API_KEY'] = gemini_key
                os.environ['GOOGLE_API_KEY'] = gemini_key  # Backward compatibility
                logger.info("✅ GEMINI_API_KEY loaded directly from Secret Manager")
                return gemini_key
        except Exception as e:
            logger.warning(f"Failed to load from Secret Manager: {e}")
        
        # Method 4: Try manual script execution
        try:
            gemini_key = self._load_via_script()
            if gemini_key:
                os.environ['GEMINI_API_KEY'] = gemini_key
                os.environ['GOOGLE_API_KEY'] = gemini_key  # Backward compatibility
                logger.info("✅ GEMINI_API_KEY loaded via script execution")
                return gemini_key
        except Exception as e:
            logger.warning(f"Failed to load via script: {e}")
        
        logger.error("❌ All fallback methods failed to load GEMINI_API_KEY")
        return None
    
    def _load_from_persistent_cache(self) -> Optional[str]:
        """Load GEMINI_API_KEY from persistent cache"""
        cache_dir = Path.home() / ".claude" / "env_cache"
        cache_file = cache_dir / "api_keys.json"
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        api_keys = cache_data.get("api_keys", {})
        return api_keys.get("GEMINI_API_KEY")
    
    def _load_from_secret_manager(self) -> Optional[str]:
        """Load GEMINI_API_KEY directly from Google Secret Manager"""
        try:
            from google.cloud import secretmanager
            
            client = secretmanager.SecretManagerServiceClient()
            secret_path = "projects/custom-mix-460500-g9/secrets/gemini-api-key/versions/latest"
            
            response = client.access_secret_version(request={"name": secret_path})
            return response.payload.data.decode("UTF-8")
            
        except ImportError:
            logger.warning("google-cloud-secret-manager not available")
            return None
        except Exception as e:
            logger.warning(f"Secret Manager access failed: {e}")
            return None
    
    def _load_via_script(self) -> Optional[str]:
        """Load GEMINI_API_KEY by executing the get-gemini-key script"""
        try:
            import subprocess
            
            # Try the get-gemini-key script
            script_path = self.project_root / "scripts" / "get-gemini-key.sh"
            
            if script_path.exists():
                result = subprocess.run(
                    [str(script_path)], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                if result.returncode == 0:
                    api_key = result.stdout.strip()
                    if api_key and len(api_key) > 10:
                        return api_key
            
            # Try gcloud command directly
            result = subprocess.run([
                "gcloud", "secrets", "versions", "access", "latest",
                "--secret=gemini-api-key",
                "--project=custom-mix-460500-g9"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                api_key = result.stdout.strip()
                if api_key and len(api_key) > 10:
                    return api_key
            
            return None
            
        except Exception as e:
            logger.warning(f"Script execution failed: {e}")
            return None
    
    def ensure_openevolve_ready(self) -> Dict[str, any]:
        """
        Ensure OpenEvolve workflow is ready with all required API keys
        
        Returns:
            Status dictionary with success and details
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'gemini_api_key_available': False,
            'openevolve_ready': False,
            'methods_tried': [],
            'environment_vars_set': [],
            'errors': []
        }
        
        try:
            # Emergency load GEMINI_API_KEY
            gemini_key = self.emergency_load_gemini_key()
            
            if gemini_key:
                status['gemini_api_key_available'] = True
                status['environment_vars_set'].extend(['GEMINI_API_KEY', 'GOOGLE_API_KEY'])
                
                # Test API key validity
                if self._test_gemini_api_key(gemini_key):
                    status['success'] = True
                    status['openevolve_ready'] = True
                    logger.info("✅ OpenEvolve workflow is ready with valid GEMINI_API_KEY")
                else:
                    status['errors'].append("GEMINI_API_KEY validation failed")
                    logger.error("❌ GEMINI_API_KEY validation failed")
            else:
                status['errors'].append("Could not obtain GEMINI_API_KEY from any source")
                logger.error("❌ Could not obtain GEMINI_API_KEY from any source")
            
        except Exception as e:
            error_msg = f"Exception during OpenEvolve readiness check: {e}"
            status['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return status
    
    def _test_gemini_api_key(self, api_key: str) -> bool:
        """Test if GEMINI_API_KEY is valid"""
        try:
            import requests
            
            url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            response = requests.get(url, timeout=10)
            
            return response.status_code == 200
            
        except ImportError:
            # If requests is not available, assume key is valid
            logger.warning("requests not available, assuming API key is valid")
            return True
        except Exception as e:
            logger.warning(f"API key test failed: {e}")
            return False
    
    def generate_openevolve_env_file(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Generate environment file for OpenEvolve workflow
        
        Args:
            output_path: Optional path for the environment file
            
        Returns:
            Path to generated environment file or None if failed
        """
        try:
            if not output_path:
                output_path = self.project_root / ".claude" / "utils" / "openevolve.env"
            
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get GEMINI_API_KEY
            gemini_key = self.emergency_load_gemini_key()
            if not gemini_key:
                logger.error("❌ Cannot generate environment file without GEMINI_API_KEY")
                return None
            
            # Generate environment file content
            env_content = f"""# OpenEvolve Environment Variables
# Generated: {datetime.now().isoformat()}

# Gemini API Keys (backward compatible)
GEMINI_API_KEY={gemini_key}
GOOGLE_API_KEY={gemini_key}

# OpenEvolve Configuration
OPENEVOLVE_ENABLED=true
OPENEVOLVE_PROJECT_ID=custom-mix-460500-g9
OPENEVOLVE_LITELLM_PROXY_URL=http://localhost:4001/v1

# Session Information
CLAUDE_SESSION_ID={os.environ.get('CLAUDE_SESSION_ID', 'unknown')}
OPENEVOLVE_SESSION_START={datetime.now().isoformat()}
"""
            
            # Write environment file
            with open(output_path, 'w') as f:
                f.write(env_content)
            
            logger.info(f"✅ OpenEvolve environment file generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Failed to generate OpenEvolve environment file: {e}")
            return None


def openevolve_emergency_init() -> Dict[str, any]:
    """
    Emergency initialization function for OpenEvolve workflows
    
    Returns:
        Status dictionary
    """
    logger.info("🚨 OpenEvolve Emergency API Keys Initialization")
    
    fallback = OpenEvolveAPIKeysFallback()
    status = fallback.ensure_openevolve_ready()
    
    if status['success']:
        logger.info("✅ OpenEvolve emergency initialization successful")
        
        # Generate environment file for future use
        env_file = fallback.generate_openevolve_env_file()
        if env_file:
            status['env_file_generated'] = str(env_file)
    else:
        logger.error("❌ OpenEvolve emergency initialization failed")
        logger.error(f"Errors: {', '.join(status['errors'])}")
    
    return status


def main():
    """Test the OpenEvolve API keys fallback system"""
    print("🚨 OpenEvolve API Keys Fallback System")
    print("=" * 50)
    
    # Test emergency initialization
    status = openevolve_emergency_init()
    
    # Display results
    print(f"\n📊 Emergency Initialization Result:")
    print(f"   Success: {'✅' if status['success'] else '❌'}")
    print(f"   GEMINI_API_KEY Available: {'✅' if status['gemini_api_key_available'] else '❌'}")
    print(f"   OpenEvolve Ready: {'✅' if status['openevolve_ready'] else '❌'}")
    
    if status['environment_vars_set']:
        print(f"   Environment Variables Set: {', '.join(status['environment_vars_set'])}")
    
    if status['errors']:
        print(f"\n❌ Errors:")
        for error in status['errors']:
            print(f"   - {error}")
    
    # Test current environment
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        print(f"\n🔑 GEMINI_API_KEY: Available ({len(gemini_key)} chars)")
    else:
        print(f"\n❌ GEMINI_API_KEY: Not available in environment")
    
    # Save status report
    report_path = Path("openevolve_fallback_report.json")
    with open(report_path, 'w') as f:
        json.dump(status, f, indent=2)
    print(f"\n📋 Detailed report saved to: {report_path}")
    
    return status['success']


if __name__ == "__main__":
    main()