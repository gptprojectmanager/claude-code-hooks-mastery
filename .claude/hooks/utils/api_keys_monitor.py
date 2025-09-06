#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "google-cloud-secret-manager",
# ]
# ///

"""
API Keys Monitoring System
===========================

Comprehensive monitoring system for API keys in Claude Code environment.
Provides real-time status, health checks, and automatic recovery.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APIKeysMonitor:
    """Comprehensive API keys monitoring and health checking system"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.monitor_cache = Path.home() / ".claude" / "monitor_cache"
        self.monitor_cache.mkdir(parents=True, exist_ok=True)
        
        self.required_keys = ['GEMINI_API_KEY']
        self.optional_keys = ['GOOGLE_API_KEY',  'FIRECRAWL_API_KEY']
        self.all_keys = self.required_keys + self.optional_keys
        
    def get_comprehensive_status(self) -> Dict:
        """Get comprehensive status of all API keys and related systems"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'session_id': os.environ.get('CLAUDE_SESSION_ID', 'unknown'),
            'environment': {
                'working_directory': os.getcwd(),
                'python_version': sys.version.split()[0],
                'user_home': str(Path.home())
            },
            'api_keys': self._check_api_keys_status(),
            'persistence_system': self._check_persistence_system(),
            'secret_manager': self._check_secret_manager_access(),
            'validation_results': self._run_validation_tests(),
            'recovery_status': self._check_recovery_capabilities(),
            'openevolve_readiness': self._check_openevolve_readiness()
        }
        
        # Calculate overall health score
        status['health_score'] = self._calculate_health_score(status)
        status['recommendations'] = self._generate_recommendations(status)
        
        return status
    
    def _check_api_keys_status(self) -> Dict:
        """Check status of all API keys in environment"""
        api_keys_status = {}
        
        for key in self.all_keys:
            value = os.environ.get(key)
            
            if value:
                api_keys_status[key] = {
                    'available': True,
                    'length': len(value),
                    'valid_format': len(value) > 10 and not value.isspace(),
                    'prefix': value[:5] + '...' if len(value) > 5 else value,
                    'last_modified': self._get_env_var_timestamp(key)
                }
            else:
                api_keys_status[key] = {
                    'available': False,
                    'length': 0,
                    'valid_format': False,
                    'prefix': None,
                    'last_modified': None
                }
        
        return api_keys_status
    
    def _check_persistence_system(self) -> Dict:
        """Check status of persistence system components"""
        persistence_status = {
            'cache_directory_exists': False,
            'cache_file_exists': False,
            'cache_file_age_hours': None,
            'persistent_env_manager_available': False,
            'auto_init_available': False
        }
        
        # Check cache directory
        cache_dir = Path.home() / ".claude" / "env_cache"
        persistence_status['cache_directory_exists'] = cache_dir.exists()
        
        # Check cache file
        cache_file = cache_dir / "api_keys.json"
        if cache_file.exists():
            persistence_status['cache_file_exists'] = True
            
            try:
                # Calculate cache age
                cache_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = datetime.now() - cache_mtime
                persistence_status['cache_file_age_hours'] = age.total_seconds() / 3600
            except Exception:
                pass
        
        # Check component availability
        try:
            sys.path.insert(0, str(self.script_dir))
            from persistent_env_manager import PersistentEnvManager
            persistence_status['persistent_env_manager_available'] = True
        except ImportError:
            pass
        
        try:
            from auto_init_api_keys import auto_initialize
            persistence_status['auto_init_available'] = True
        except ImportError:
            pass
        
        return persistence_status
    
    def _check_secret_manager_access(self) -> Dict:
        """Check Google Secret Manager access status"""
        secret_manager_status = {
            'gcloud_authenticated': False,
            'secret_manager_accessible': False,
            'gemini_secret_accessible': False,
            'response_time_ms': None,
            'last_error': None
        }
        
        try:
            # Check gcloud authentication
            import subprocess
            result = subprocess.run(['gcloud', 'auth', 'list', '--quiet'], 
                                  capture_output=True, text=True, timeout=10)
            secret_manager_status['gcloud_authenticated'] = result.returncode == 0
            
            # Test Secret Manager access
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            secret_manager_status['secret_manager_accessible'] = True
            
            # Test specific secret access
            secret_path = "projects/custom-mix-460500-g9/secrets/gemini-api-key/versions/latest"
            start_time = time.time()
            
            response = client.access_secret_version(request={"name": secret_path})
            response_time = (time.time() - start_time) * 1000
            
            secret_manager_status['response_time_ms'] = response_time
            secret_manager_status['gemini_secret_accessible'] = True
            
        except ImportError as e:
            secret_manager_status['last_error'] = f"Import error: {e}"
        except Exception as e:
            secret_manager_status['last_error'] = str(e)
        
        return secret_manager_status
    
    def _run_validation_tests(self) -> Dict:
        """Run API validation tests"""
        validation_results = {}
        
        try:
            sys.path.insert(0, str(self.script_dir))
            from api_keys_validator import APIKeyValidator
            
            validator = APIKeyValidator()
            validation_results = validator.validate_all_keys()
            
        except ImportError as e:
            validation_results = {'error': f'Validator not available: {e}'}
        except Exception as e:
            validation_results = {'error': f'Validation failed: {e}'}
        
        return validation_results
    
    def _check_recovery_capabilities(self) -> Dict:
        """Check recovery and fallback capabilities"""
        recovery_status = {
            'session_start_hook_available': False,
            'fallback_scripts_available': False,
            'manual_recovery_possible': False,
            'openevolve_fallback_available': False
        }
        
        # Check SessionStart hook
        session_start_path = self.script_dir.parent / "session_start.py"
        recovery_status['session_start_hook_available'] = session_start_path.exists()
        
        # Check fallback scripts
        fallback_paths = [
            self.script_dir / "api_keys_initializer.py",
            self.script_dir / "persistent_env_manager.py",
            self.script_dir / "auto_init_api_keys.py"
        ]
        recovery_status['fallback_scripts_available'] = all(p.exists() for p in fallback_paths)
        
        # Check manual recovery capability (gcloud + scripts)
        try:
            import subprocess
            gcloud_result = subprocess.run(['which', 'gcloud'], capture_output=True)
            recovery_status['manual_recovery_possible'] = gcloud_result.returncode == 0
        except Exception:
            pass
        
        # Check OpenEvolve fallback
        openevolve_fallback_path = self.script_dir / "openevolve_api_keys_fallback.py"
        recovery_status['openevolve_fallback_available'] = openevolve_fallback_path.exists()
        
        return recovery_status
    
    def _check_openevolve_readiness(self) -> Dict:
        """Check OpenEvolve system readiness"""
        openevolve_status = {
            'gemini_key_available': False,
            'litellm_config_exists': False,
            'environment_file_exists': False,
            'ready_for_optimization': False
        }
        
        # Check GEMINI_API_KEY
        gemini_key = os.environ.get('GEMINI_API_KEY')
        openevolve_status['gemini_key_available'] = bool(gemini_key and len(gemini_key) > 10)
        
        # Check LiteLLM config
        litellm_config_path = self.script_dir.parent.parent / "utils" / "openevolve_litellm_gemini_config.yaml"
        openevolve_status['litellm_config_exists'] = litellm_config_path.exists()
        
        # Check environment file
        env_file_path = self.script_dir.parent / "utils" / "openevolve.env"
        openevolve_status['environment_file_exists'] = env_file_path.exists()
        
        # Overall readiness
        openevolve_status['ready_for_optimization'] = (
            openevolve_status['gemini_key_available'] and
            openevolve_status['litellm_config_exists']
        )
        
        return openevolve_status
    
    def _get_env_var_timestamp(self, env_var: str) -> Optional[str]:
        """Get estimated timestamp for when environment variable was set"""
        # This is a placeholder - environment variables don't have timestamps
        # In a real implementation, we might track this in our persistence system
        return datetime.now().isoformat()
    
    def _calculate_health_score(self, status: Dict) -> int:
        """Calculate overall health score (0-100)"""
        score = 0
        max_score = 100
        
        # API Keys (40 points)
        api_keys = status['api_keys']
        required_keys_available = sum(1 for key in self.required_keys 
                                    if api_keys.get(key, {}).get('available', False))
        score += (required_keys_available / len(self.required_keys)) * 40
        
        # Persistence System (20 points)
        persistence = status['persistence_system']
        if persistence['persistent_env_manager_available']:
            score += 10
        if persistence['cache_file_exists']:
            score += 10
        
        # Secret Manager Access (20 points)
        secret_manager = status['secret_manager']
        if secret_manager['secret_manager_accessible']:
            score += 10
        if secret_manager['gemini_secret_accessible']:
            score += 10
        
        # Validation Success (10 points)
        validation = status['validation_results']
        if not isinstance(validation, dict) or 'error' not in validation:
            gemini_valid = validation.get('GEMINI_API_KEY', {}).get('valid', False)
            if gemini_valid:
                score += 10
        
        # Recovery Capabilities (10 points)
        recovery = status['recovery_status']
        if recovery['fallback_scripts_available']:
            score += 5
        if recovery['openevolve_fallback_available']:
            score += 5
        
        return min(int(score), max_score)
    
    def _generate_recommendations(self, status: Dict) -> List[str]:
        """Generate recommendations based on status"""
        recommendations = []
        
        # Check critical issues
        api_keys = status['api_keys']
        if not api_keys.get('GEMINI_API_KEY', {}).get('available', False):
            recommendations.append("CRITICAL: Run API key initialization - GEMINI_API_KEY missing")
        
        # Check persistence issues
        persistence = status['persistence_system']
        if not persistence['cache_file_exists']:
            recommendations.append("Create persistent API keys cache for better reliability")
        
        cache_age = persistence.get('cache_file_age_hours')
        if cache_age and cache_age > 24:
            recommendations.append(f"Refresh API keys cache (age: {cache_age:.1f}h)")
        
        # Check validation issues
        validation = status['validation_results']
        if isinstance(validation, dict) and 'error' in validation:
            recommendations.append("Fix API key validation system")
        
        # Check Secret Manager issues
        secret_manager = status['secret_manager']
        if not secret_manager['gcloud_authenticated']:
            recommendations.append("Run 'gcloud auth login' to authenticate with Google Cloud")
        
        # Check OpenEvolve readiness
        openevolve = status['openevolve_readiness']
        if not openevolve['ready_for_optimization']:
            recommendations.append("Configure OpenEvolve system for code optimization workflows")
        
        return recommendations
    
    def save_monitoring_report(self, status: Dict) -> Path:
        """Save monitoring report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.monitor_cache / f"api_keys_monitor_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        return report_file
    
    def run_continuous_monitoring(self, interval_minutes: int = 15, max_iterations: int = 96) -> None:
        """Run continuous monitoring with specified interval"""
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval_minutes}min, max: {max_iterations} iterations)")
        
        for iteration in range(max_iterations):
            try:
                status = self.get_comprehensive_status()
                report_file = self.save_monitoring_report(status)
                
                health_score = status['health_score']
                recommendations_count = len(status['recommendations'])
                
                logger.info(f"📊 Monitoring iteration {iteration + 1}: Health Score {health_score}/100, {recommendations_count} recommendations")
                
                if health_score < 80:
                    logger.warning(f"⚠️ Low health score detected: {health_score}/100")
                    for rec in status['recommendations'][:3]:  # Show top 3 recommendations
                        logger.warning(f"   💡 {rec}")
                
                # Sleep until next iteration
                if iteration < max_iterations - 1:
                    time.sleep(interval_minutes * 60)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring iteration failed: {e}")
                time.sleep(60)  # Wait 1 minute before retry


def main():
    """Test the API keys monitoring system"""
    print("📊 API Keys Monitoring System")
    print("=" * 50)
    
    monitor = APIKeysMonitor()
    
    # Get comprehensive status
    print("🔍 Running comprehensive status check...")
    status = monitor.get_comprehensive_status()
    
    # Display summary
    print(f"\n📋 System Status Summary:")
    print(f"   Timestamp: {status['timestamp']}")
    print(f"   Session ID: {status['session_id']}")
    print(f"   Health Score: {status['health_score']}/100")
    
    # Display API keys status
    print(f"\n🔑 API Keys Status:")
    for key, info in status['api_keys'].items():
        status_icon = "✅" if info['available'] else "❌"
        print(f"   {key}: {status_icon} ({'Available' if info['available'] else 'Missing'})")
    
    # Display validation results
    validation = status['validation_results']
    if not isinstance(validation, dict) or 'error' not in validation:
        print(f"\n🧪 Validation Results:")
        for key, result in validation.items():
            if isinstance(result, dict):
                valid_icon = "✅" if result.get('valid', False) else "❌"
                print(f"   {key}: {valid_icon} {result.get('message', 'No message')}")
    
    # Display recommendations
    if status['recommendations']:
        print(f"\n💡 Recommendations ({len(status['recommendations'])}):")
        for i, rec in enumerate(status['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # Display OpenEvolve readiness
    openevolve = status['openevolve_readiness']
    print(f"\n🔬 OpenEvolve Readiness:")
    print(f"   GEMINI_API_KEY Available: {'✅' if openevolve['gemini_key_available'] else '❌'}")
    print(f"   LiteLLM Config Exists: {'✅' if openevolve['litellm_config_exists'] else '❌'}")
    print(f"   Ready for Optimization: {'✅' if openevolve['ready_for_optimization'] else '❌'}")
    
    # Save report
    report_file = monitor.save_monitoring_report(status)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return status['health_score'] >= 80


if __name__ == "__main__":
    main()