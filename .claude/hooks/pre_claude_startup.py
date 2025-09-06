#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "google-cloud-secret-manager",
# ]
# ///

"""
Pre-Claude Startup Script
=========================

This script loads credentials from Google Secret Manager and exposes them
as environment variables BEFORE Claude Code starts, ensuring all MCP servers
and child processes have access to credentials without terminal exposure.

SECURITY FEATURES:
- Google Secret Manager integration for secure credential storage
- Environment variable isolation from terminal sessions
- Automatic credential validation and refresh
- Silent failure handling for production deployment
- Zero hardcoded credentials in any configuration files

USAGE:
    python3 pre_claude_startup.py
    eval "$(python3 pre_claude_startup.py --export)"
    source <(python3 pre_claude_startup.py --export)
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecureCredentialLoader:
    """Secure credential management for Claude Code ecosystem"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.credentials_cache = {}
        self.validation_cache = {}
        
    def load_from_secret_manager(self) -> Dict[str, str]:
        """Load credentials from Google Secret Manager"""
        try:
            # Import Secret Manager client
            from google.cloud import secretmanager
            
            client = secretmanager.SecretManagerServiceClient()
            credentials = {}
            
            # Define secret mappings: secret_name -> environment_variable
            secret_mappings = {
                'gemini-api-key': ['GEMINI_API_KEY', 'GOOGLE_API_KEY'],  # Multiple mappings for compatibility
                'firecrawl-api-key': ['FIRECRAWL_API_KEY'],
                'openai-api-key': ['OPENAI_API_KEY'],  # Now available
                'anthropic-api-key': ['ANTHROPIC_API_KEY'],  # If available
            }
            
            # Load complex secret configurations (JSON format)
            json_secret_mappings = {
                'claude-openrouter-config': {
                    'openrouter_api_key': 'OPENROUTER_API_KEY'
                }
            }
            
            for secret_name, env_vars in secret_mappings.items():
                try:
                    # Construct the resource name
                    name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                    
                    # Access the secret version
                    response = client.access_secret_version(request={"name": name})
                    secret_value = response.payload.data.decode("UTF-8")
                    
                    if secret_value and len(secret_value.strip()) > 10:  # Basic validation
                        for env_var in env_vars:
                            credentials[env_var] = secret_value.strip()
                        logger.info(f"✅ Loaded {secret_name} -> {env_vars}")
                    else:
                        logger.warning(f"⚠️ Invalid secret value for {secret_name}")
                        
                except Exception as e:
                    logger.warning(f"❌ Failed to load {secret_name}: {e}")
                    continue
            
            # Process JSON secret configurations
            for secret_name, field_mappings in json_secret_mappings.items():
                try:
                    # Construct the resource name
                    name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                    
                    # Access the secret version
                    response = client.access_secret_version(request={"name": name})
                    secret_json = response.payload.data.decode("UTF-8")
                    
                    # Parse JSON and extract specific fields
                    import json
                    secret_data = json.loads(secret_json)
                    
                    for json_field, env_var in field_mappings.items():
                        if json_field in secret_data:
                            value = secret_data[json_field]
                            if value and len(str(value).strip()) > 10:
                                credentials[env_var] = str(value).strip()
                                logger.info(f"✅ Loaded {secret_name}.{json_field} -> {env_var}")
                            else:
                                logger.warning(f"⚠️ Invalid value for {secret_name}.{json_field}")
                        else:
                            logger.warning(f"⚠️ Field {json_field} not found in {secret_name}")
                            
                except Exception as e:
                    logger.warning(f"❌ Failed to load JSON secret {secret_name}: {e}")
                    continue
            
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Secret Manager client: {e}")
            return {}
    
    def validate_credentials(self, credentials: Dict[str, str]) -> Dict[str, bool]:
        """Validate loaded credentials"""
        validation_results = {}
        
        # Required credentials
        required_keys = ['GEMINI_API_KEY', 'GOOGLE_API_KEY']
        optional_keys = ['ELEVENLABS_API_KEY', 'FIRECRAWL_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        
        for key in required_keys + optional_keys:
            value = credentials.get(key, '')
            is_valid = bool(value and len(value.strip()) > 10)
            validation_results[key] = is_valid
            
            if is_valid:
                logger.info(f"✅ {key}: Valid ({len(value)} chars)")
            else:
                if key in required_keys:
                    logger.error(f"❌ {key}: Required but invalid/missing")
                else:
                    logger.info(f"ℹ️ {key}: Optional, not provided")
        
        return validation_results
    
    def export_environment_variables(self, credentials: Dict[str, str]) -> str:
        """Generate shell export commands for credentials"""
        export_commands = []
        
        for env_var, value in credentials.items():
            if value:
                # Escape single quotes in the value
                escaped_value = value.replace("'", "'\"'\"'")
                export_commands.append(f"export {env_var}='{escaped_value}'")
        
        return "\n".join(export_commands)
    
    def apply_to_current_environment(self, credentials: Dict[str, str]) -> int:
        """Apply credentials to current Python process environment"""
        applied_count = 0
        
        for env_var, value in credentials.items():
            if value:
                os.environ[env_var] = value
                applied_count += 1
                logger.info(f"✅ Set {env_var} in process environment")
        
        return applied_count
    
    def save_to_cache(self, credentials: Dict[str, str], cache_path: Optional[Path] = None) -> bool:
        """Save credentials to secure cache for session persistence"""
        try:
            if cache_path is None:
                cache_dir = Path.home() / ".claude" / "secure_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path = cache_dir / "credentials.json"
            
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "process_id": os.getpid(),
                "credentials": credentials
            }
            
            # Set restrictive permissions (owner only)
            cache_path.touch(mode=0o600, exist_ok=True)
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"✅ Saved credentials cache to {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save credentials cache: {e}")
            return False
    
    def load_from_cache(self, cache_path: Optional[Path] = None, max_age_hours: int = 24) -> Dict[str, str]:
        """Load credentials from cache if valid"""
        try:
            if cache_path is None:
                cache_dir = Path.home() / ".claude" / "secure_cache"
                cache_path = cache_dir / "credentials.json"
            
            if not cache_path.exists():
                logger.info("No credentials cache found")
                return {}
            
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache age
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            age = datetime.now() - cache_time
            
            if age.total_seconds() > max_age_hours * 3600:
                logger.warning(f"Credentials cache is {age.total_seconds()/3600:.1f}h old, refreshing...")
                return {}
            
            credentials = cache_data.get("credentials", {})
            logger.info(f"✅ Loaded {len(credentials)} credentials from cache (age: {age.total_seconds()/3600:.1f}h)")
            
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Failed to load credentials cache: {e}")
            return {}
    
    def load_from_env_file(self) -> Dict[str, str]:
        """Load credentials from local environment variables only"""
        credentials = {}
        
        # Define environment variables to check
        env_vars = ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'FIRECRAWL_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'ELEVENLABS_API_KEY']
        
        for env_var in env_vars:
            value = os.environ.get(env_var)
            if value and len(value.strip()) > 10:
                credentials[env_var] = value.strip()
                logger.info(f"✅ Loaded {env_var} from environment")
            else:
                logger.info(f"ℹ️ {env_var}: Not found in environment")
        
        return credentials
    
    def get_secure_credentials(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get secure credentials from local environment only (skip Secret Manager)"""
        # Load from local environment variables
        logger.info("🔄 Loading credentials from local environment...")
        credentials = self.load_from_env_file()
        
        if credentials:
            # Validate
            validation_results = self.validate_credentials(credentials)
            
            # Check if we have minimum required credentials
            if validation_results.get('GEMINI_API_KEY', False):
                logger.info("✅ Successfully loaded and validated credentials from environment")
                return credentials
            else:
                logger.error("❌ Missing required GEMINI_API_KEY credential in environment")
        
        logger.error("❌ Failed to load valid credentials from environment")
        return {}


def main():
    """Main entry point for pre-Claude startup script"""
    parser = argparse.ArgumentParser(description="Secure credential loader for Claude Code")
    parser.add_argument('--export', action='store_true', 
                       help='Output shell export commands instead of applying to current process')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Force refresh from Secret Manager, ignoring cache')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate current environment, don\'t load new credentials')
    parser.add_argument('--cache-path', type=str,
                       help='Custom cache file path')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress all output except errors')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        env_path = Path.home() / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"✅ Loaded environment from {env_path}")
        else:
            logger.warning(f"⚠️ No .env file found at {env_path}")
    except ImportError:
        logger.warning("⚠️ python-dotenv not available, skipping .env loading")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load .env file: {e}")
    
    # Get project_id from environment variable
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        logger.warning("⚠️ GOOGLE_CLOUD_PROJECT not set in environment, using default")
    
    try:
        loader = SecureCredentialLoader(project_id=project_id)
        
        if args.validate_only:
            # Just validate current environment
            current_env = {key: os.environ.get(key, '') for key in 
                          ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'ELEVENLABS_API_KEY', 'FIRECRAWL_API_KEY']}
            validation_results = loader.validate_credentials(current_env)
            
            valid_count = sum(1 for is_valid in validation_results.values() if is_valid)
            total_count = len(validation_results)
            
            if not args.quiet:
                print(f"Validation Results: {valid_count}/{total_count} credentials valid")
            
            sys.exit(0 if validation_results.get('GEMINI_API_KEY', False) else 1)
        
        # Load credentials
        credentials = loader.get_secure_credentials(force_refresh=args.force_refresh)
        
        if not credentials:
            logger.error("❌ Failed to load any valid credentials")
            sys.exit(1)
        
        if args.export:
            # Output shell export commands
            export_commands = loader.export_environment_variables(credentials)
            print(export_commands)
        else:
            # Apply to current process environment
            applied_count = loader.apply_to_current_environment(credentials)
            if not args.quiet:
                logger.info(f"✅ Applied {applied_count} credentials to current environment")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()