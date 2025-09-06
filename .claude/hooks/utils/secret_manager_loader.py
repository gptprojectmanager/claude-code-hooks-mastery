#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
# ]
# ///

"""
Google Secret Manager API Key Loader
====================================

This utility provides secure API key loading from Google Secret Manager
for MCP server configurations and other components.
"""

import os
import sys
import logging
from typing import Optional, Dict
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretManagerLoader:
    """Load API keys from Google Secret Manager with fallback support"""
    
    def __init__(self, project_id: str = "custom-mix-460500-g9"):
        self.project_id = project_id
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Secret Manager client"""
        try:
            self.client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Secret Manager client: {e}")
            self.client = None
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from Google Secret Manager with fallback support.
        
        Args:
            secret_name: Name of the secret in Secret Manager
            fallback_env_var: Environment variable to use as fallback
            
        Returns:
            The secret value or None if not found
        """
        # Try Secret Manager first
        if self.client:
            try:
                secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                response = self.client.access_secret_version(request={"name": secret_path})
                secret_value = response.payload.data.decode("UTF-8")
                logger.info(f"Retrieved {secret_name} from Secret Manager")
                return secret_value
                
            except Exception as e:
                logger.warning(f"Failed to retrieve {secret_name} from Secret Manager: {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            env_value = os.getenv(fallback_env_var)
            if env_value:
                logger.info(f"Using {secret_name} from environment variable {fallback_env_var}")
                return env_value
        
        logger.error(f"Could not retrieve {secret_name} from any source")
        return None
    
    def get_all_api_keys(self) -> Dict[str, Optional[str]]:
        """
        Retrieve all configured API keys.
        
        Returns:
            Dictionary mapping service names to API keys
        """
        api_keys = {
            'firecrawl': self.get_secret('firecrawl-api-key', 'FIRECRAWL_API_KEY'),
            'gemini': self.get_secret('gemini-api-key', 'GEMINI_API_KEY'),
            'openai': self.get_secret('openai-api-key', 'OPENAI_API_KEY')
        }
        
        return api_keys


def main():
    """Test the Secret Manager loader"""
    loader = SecretManagerLoader()
    
    print("🔐 Testing Secret Manager API Key Loader")
    print("=" * 50)
    
    # Test individual secrets
    secrets_to_test = ['elevenlabs-api-key', 'firecrawl-api-key', 'gemini-api-key', 'openai-api-key']
    
    for secret_name in secrets_to_test:
        result = loader.get_secret(secret_name)
        if result:
            print(f"✅ {secret_name}: Retrieved successfully ({len(result)} chars)")
        else:
            print(f"❌ {secret_name}: Failed to retrieve")
    
    print("\n🔍 All API Keys Summary:")
    all_keys = loader.get_all_api_keys()
    for service, key in all_keys.items():
        status = "✅ Available" if key else "❌ Missing"
        print(f"   {service}: {status}")


if __name__ == "__main__":
    main()