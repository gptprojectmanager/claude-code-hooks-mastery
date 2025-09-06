#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "google-cloud-secret-manager",
# ]
# ///

"""
Real-Time API Keys Validator
============================

Comprehensive validation and testing of API keys for Claude Code environment.
Provides real-time validation and automatic recovery mechanisms.
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APIKeyValidator:
    """Comprehensive API key validation and testing"""
    
    def __init__(self):
        self.results = {}
        self.session = requests.Session()
        self.session.timeout = 10
        
    def validate_gemini_key(self, api_key: str) -> Tuple[bool, str, Dict]:
        """
        Validate Gemini API key by testing actual API access
        
        Returns:
            (is_valid, message, metadata)
        """
        try:
            # Test with models list endpoint
            url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            
            start_time = time.time()
            response = self.session.get(url)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_count = len(models)
                
                return True, f"Valid - {model_count} models available", {
                    'response_time': response_time,
                    'model_count': model_count,
                    'status_code': response.status_code
                }
            else:
                return False, f"Invalid - HTTP {response.status_code}", {
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'error': response.text[:200]
                }
                
        except requests.RequestException as e:
            return False, f"Network error: {str(e)[:100]}", {
                'error_type': 'network',
                'error': str(e)
            }
        except Exception as e:
            return False, f"Validation error: {str(e)[:100]}", {
                'error_type': 'validation',
                'error': str(e)
            }
    
    def validate_elevenlabs_key(self, api_key: str) -> Tuple[bool, str, Dict]:
        """Validate ElevenLabs API key"""
        try:
            url = "https://api.elevenlabs.io/v1/user"
            headers = {"xi-api-key": api_key}
            
            start_time = time.time()
            response = self.session.get(url, headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return True, "Valid ElevenLabs API key", {
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            else:
                return False, f"Invalid - HTTP {response.status_code}", {
                    'response_time': response_time,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return False, f"Error: {str(e)[:100]}", {'error': str(e)}
    
    def validate_firecrawl_key(self, api_key: str) -> Tuple[bool, str, Dict]:
        """Validate Firecrawl API key"""
        try:
            # Firecrawl doesn't have a simple validation endpoint
            # So we just check if the key format looks valid
            if api_key and len(api_key) > 10 and api_key.startswith(('fc-', 'sk-')):
                return True, "Key format appears valid", {
                    'length': len(api_key),
                    'prefix': api_key[:5] + '...'
                }
            else:
                return False, "Invalid key format", {
                    'length': len(api_key) if api_key else 0
                }
                
        except Exception as e:
            return False, f"Error: {str(e)[:100]}", {'error': str(e)}
    
    def validate_all_keys(self) -> Dict[str, Dict]:
        """Validate all API keys in environment"""
        validation_results = {}
        
        # Define key validators
        key_validators = {
            'GEMINI_API_KEY': self.validate_gemini_key,
            'GOOGLE_API_KEY': self.validate_gemini_key,
            
            'FIRECRAWL_API_KEY': self.validate_firecrawl_key
        }
        
        for env_var, validator_func in key_validators.items():
            api_key = os.environ.get(env_var)
            
            if not api_key:
                validation_results[env_var] = {
                    'valid': False,
                    'message': 'Not found in environment',
                    'metadata': {'length': 0}
                }
                continue
            
            try:
                is_valid, message, metadata = validator_func(api_key)
                validation_results[env_var] = {
                    'valid': is_valid,
                    'message': message,
                    'metadata': metadata,
                    'key_length': len(api_key)
                }
            except Exception as e:
                validation_results[env_var] = {
                    'valid': False,
                    'message': f'Validation failed: {str(e)[:100]}',
                    'metadata': {'error': str(e)},
                    'key_length': len(api_key)
                }
        
        return validation_results
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        validation_results = self.validate_all_keys()
        
        # Calculate summary statistics
        total_keys = len(validation_results)
        valid_keys = sum(1 for result in validation_results.values() if result['valid'])
        critical_keys_valid = validation_results.get('GEMINI_API_KEY', {}).get('valid', False)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_keys': total_keys,
                'valid_keys': valid_keys,
                'validation_success_rate': (valid_keys / total_keys * 100) if total_keys > 0 else 0,
                'critical_keys_status': 'PASS' if critical_keys_valid else 'FAIL'
            },
            'validation_results': validation_results,
            'recommendations': self._generate_recommendations(validation_results),
            'environment_info': {
                'python_version': sys.version.split()[0],
                'working_directory': os.getcwd(),
                'claude_session_id': os.environ.get('CLAUDE_SESSION_ID', 'unknown')
            }
        }
        
        return report
    
    def _generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check for missing critical keys
        if not validation_results.get('GEMINI_API_KEY', {}).get('valid', False):
            recommendations.append(
                "CRITICAL: GEMINI_API_KEY is missing or invalid. Run API key initialization."
            )
        
        # Check for backward compatibility
        gemini_valid = validation_results.get('GEMINI_API_KEY', {}).get('valid', False)
        google_valid = validation_results.get('GOOGLE_API_KEY', {}).get('valid', False)
        
        if gemini_valid and not google_valid:
            recommendations.append(
                "Set GOOGLE_API_KEY to same value as GEMINI_API_KEY for backward compatibility."
            )
        
        # Check response times
        gemini_metadata = validation_results.get('GEMINI_API_KEY', {}).get('metadata', {})
        response_time = gemini_metadata.get('response_time', 0)
        
        if response_time > 5.0:
            recommendations.append(
                f"Gemini API response time is high ({response_time:.1f}s). Check network connection."
            )
        
        # Check for missing optional keys
        optional_keys = [ 'FIRECRAWL_API_KEY']
        missing_optional = [
            key for key in optional_keys 
            if not validation_results.get(key, {}).get('valid', False)
        ]
        
        if missing_optional:
            recommendations.append(
                f"Optional API keys missing: {', '.join(missing_optional)}"
            )
        
        return recommendations


def ensure_api_keys_with_validation() -> Tuple[bool, Dict]:
    """
    Ensure API keys are available with comprehensive validation
    
    Returns:
        (success, validation_report)
    """
    try:
        # Import API keys initializer
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        from api_keys_initializer import initialize_api_keys
        
        # Initialize API keys
        success, status = initialize_api_keys()
        
        if not success:
            logger.error("❌ API keys initialization failed")
            return False, {}
        
        # Validate with comprehensive testing
        validator = APIKeyValidator()
        report = validator.generate_validation_report()
        
        # Check if validation passed
        validation_success = report['summary']['critical_keys_status'] == 'PASS'
        
        if validation_success:
            logger.info("✅ API keys validation successful")
        else:
            logger.error("❌ API keys validation failed")
        
        return validation_success, report
        
    except Exception as e:
        logger.error(f"❌ Exception during API keys validation: {e}")
        return False, {'error': str(e)}


def main():
    """Test the API keys validator"""
    print("🧪 API Keys Real-Time Validator")
    print("=" * 50)
    
    # Ensure and validate API keys
    success, report = ensure_api_keys_with_validation()
    
    if report and 'error' not in report:
        # Display summary
        summary = report['summary']
        print(f"\n📊 Validation Summary:")
        print(f"   Total Keys: {summary['total_keys']}")
        print(f"   Valid Keys: {summary['valid_keys']}")
        print(f"   Success Rate: {summary['validation_success_rate']:.1f}%")
        print(f"   Critical Status: {summary['critical_keys_status']}")
        
        # Display individual results
        print(f"\n🔍 Individual Key Results:")
        for key, result in report['validation_results'].items():
            status_icon = "✅" if result['valid'] else "❌"
            print(f"   {key}: {status_icon} {result['message']}")
        
        # Display recommendations
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Save detailed report
        report_file = Path("api_keys_validation_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📋 Detailed report saved to: {report_file}")
    
    else:
        print(f"\n❌ Validation failed: {report.get('error', 'Unknown error')}")
    
    return success


if __name__ == "__main__":
    main()