#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
#     "google-cloud-secret-manager"
# ]
# ///

"""
API Configuration System for Advanced Collective Intelligence Validation
=========================================================================

This module provides secure API key configuration with multiple sources:
1. Environment variables (highest priority)
2. Google Cloud Secret Manager (for production)
3. Local configuration files (for development)
4. Demo mode (fallback for testing)
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIConfiguration:
    """Manages API keys and configuration for validation models"""
    
    def __init__(self):
        self.config = {}
        self.load_configuration()
    
    def load_configuration(self):
        """Load API configuration from multiple sources in priority order"""
        
        # 1. Environment variables (highest priority)
        self._load_from_environment()
        
        # 2. Google Cloud Secret Manager (for production)
        self._load_from_secret_manager()
        
        # 3. Local configuration files (for development)
        self._load_from_local_config()
        
        # 4. Demo mode configuration (fallback)
        self._set_demo_fallbacks()
        
        logger.info(f"Loaded configuration with {len(self.config)} API providers")
    
    def _load_from_environment(self):
        """Load API keys from environment variables"""
        env_keys = {
            'anthropic': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'google': 'GOOGLE_API_KEY'
        }
        
        for provider, env_var in env_keys.items():
            api_key = os.getenv(env_var)
            if api_key:
                self.config[provider] = {
                    'api_key': api_key,
                    'source': 'environment',
                    'enabled': True
                }
                logger.info(f"Loaded {provider} API key from environment")
    
    def _load_from_secret_manager(self):
        """Load API keys from Google Cloud Secret Manager"""
        try:
            from google.cloud import secretmanager
            
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            
            if not project_id:
                return
            
            secrets = {
                'anthropic': 'anthropic-api-key',
                'openai': 'openai-api-key',
                'google': 'google-api-key'
            }
            
            for provider, secret_name in secrets.items():
                if provider in self.config:
                    continue  # Environment variable takes priority
                
                try:
                    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                    response = client.access_secret_version(request={"name": secret_path})
                    api_key = response.payload.data.decode("UTF-8")
                    
                    self.config[provider] = {
                        'api_key': api_key,
                        'source': 'secret_manager',
                        'enabled': True
                    }
                    logger.info(f"Loaded {provider} API key from Secret Manager")
                    
                except Exception as e:
                    logger.warning(f"Could not load {provider} key from Secret Manager: {e}")
                    
        except ImportError:
            logger.debug("Google Cloud Secret Manager not available")
    
    def _load_from_local_config(self):
        """Load API keys from local configuration files"""
        config_paths = [
            Path.home() / '.claude' / 'api_keys.yaml',
            Path.home() / '.claude' / 'api_keys.json',
            Path(__file__).parent / 'config' / 'api_keys.yaml',
            Path(__file__).parent / 'config' / 'api_keys.json'
        ]
        
        for config_path in config_paths:
            if not config_path.exists():
                continue
                
            try:
                if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                    with open(config_path, 'r') as f:
                        local_config = yaml.safe_load(f)
                else:
                    with open(config_path, 'r') as f:
                        local_config = json.load(f)
                
                for provider, config_data in local_config.items():
                    if provider in self.config:
                        continue  # Higher priority source already loaded
                    
                    if isinstance(config_data, str):
                        # Simple string API key
                        self.config[provider] = {
                            'api_key': config_data,
                            'source': str(config_path),
                            'enabled': True
                        }
                    elif isinstance(config_data, dict):
                        # Full configuration object
                        self.config[provider] = {
                            'api_key': config_data.get('api_key'),
                            'source': str(config_path),
                            'enabled': config_data.get('enabled', True)
                        }
                    
                    if self.config[provider]['api_key']:
                        logger.info(f"Loaded {provider} API key from {config_path}")
                
                break  # Use first config file found
                
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")
    
    def _set_demo_fallbacks(self):
        """Set demo mode configuration for providers without API keys"""
        demo_providers = ['anthropic', 'openai', 'google']
        
        for provider in demo_providers:
            if provider not in self.config or not self.config[provider].get('api_key'):
                self.config[provider] = {
                    'api_key': None,
                    'source': 'demo_mode',
                    'enabled': True,
                    'demo_mode': True,
                    'demo_responses': self._get_demo_responses(provider)
                }
                logger.info(f"Using demo mode for {provider}")
    
    def _get_demo_responses(self, provider: str) -> Dict[str, Any]:
        """Get demo responses for testing without real API keys"""
        base_response = {
            "performance": 75,
            "novelty": 65,
            "efficiency": 80,
            "safety": 85,
            "confidence": 0.7,
            "reasoning": f"Demo validation from {provider} model",
            "key_insights": ["Demo insight 1", "Demo insight 2"],
            "recommendations": ["Demo recommendation 1", "Demo recommendation 2"]
        }
        
        # Vary responses slightly by provider for diversity
        provider_adjustments = {
            'anthropic': {'performance': 5, 'novelty': -5},
            'openai': {'efficiency': -10, 'safety': 5},
            'google': {'novelty': 10, 'performance': -5}
        }
        
        adjustments = provider_adjustments.get(provider, {})
        for dimension, adjustment in adjustments.items():
            base_response[dimension] = max(0, min(100, base_response[dimension] + adjustment))
        
        return base_response
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider"""
        return self.config.get(provider, {}).get('api_key')
    
    def is_provider_enabled(self, provider: str) -> bool:
        """Check if a provider is enabled"""
        return self.config.get(provider, {}).get('enabled', False)
    
    def is_demo_mode(self, provider: str) -> bool:
        """Check if a provider is in demo mode"""
        return self.config.get(provider, {}).get('demo_mode', False)
    
    def get_demo_response(self, provider: str) -> Dict[str, Any]:
        """Get demo response for a provider"""
        return self.config.get(provider, {}).get('demo_responses', {})
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        summary = {}
        for provider, config in self.config.items():
            summary[provider] = {
                'enabled': config.get('enabled', False),
                'source': config.get('source', 'unknown'),
                'demo_mode': config.get('demo_mode', False),
                'has_api_key': bool(config.get('api_key'))
            }
        return summary
    
    def create_sample_config_file(self, path: Optional[Path] = None) -> Path:
        """Create a sample configuration file"""
        if path is None:
            config_dir = Path.home() / '.claude'
            config_dir.mkdir(exist_ok=True)
            path = config_dir / 'api_keys.yaml'
        
        sample_config = {
            'anthropic': {
                'api_key': 'sk-ant-your-anthropic-api-key-here',
                'enabled': True
            },
            'openai': {
                'api_key': 'sk-your-openai-api-key-here', 
                'enabled': True
            },
            'google': {
                'api_key': 'your-google-api-key-here',
                'enabled': True
            }
        }
        
        with open(path, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created sample configuration file at {path}")
        return path


# Global configuration instance
_api_config = None

def get_api_config() -> APIConfiguration:
    """Get the global API configuration instance"""
    global _api_config
    if _api_config is None:
        _api_config = APIConfiguration()
    return _api_config


if __name__ == "__main__":
    # Test the configuration system
    config = APIConfiguration()
    print("API Configuration Summary:")
    print(json.dumps(config.get_configuration_summary(), indent=2))
    
    # Create sample config file
    sample_path = config.create_sample_config_file()
    print(f"\nSample configuration created at: {sample_path}")