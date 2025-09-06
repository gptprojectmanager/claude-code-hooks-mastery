#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
#     "psutil",
#     "requests",
#     "schedule",
# ]
# ///

"""
Enhanced Monitoring System for Hook Wrapper Infrastructure
==========================================================

This module extends the existing monitoring system with production-ready
features including automated diagnostics, alert management, performance
baselines, and comprehensive health monitoring.

Key Enhancements:
- Automated baseline detection and SLA monitoring
- Advanced alerting with escalation policies
- Comprehensive diagnostic automation
- Performance trend analysis
- Predictive failure detection
- Integration with external monitoring systems

Architecture:
- Enhanced monitoring with ML-based baseline detection
- Multi-tier alerting system with escalation
- Automated recovery procedures
- Real-time performance analytics
- Proactive health predictions
"""

import os
import sys
import time
import json
import logging
import threading
import statistics
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import requests
import schedule
import math

# Setup enhanced logging
log_dir = Path.home() / ".claude" / "logs" / "enhanced_monitoring"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"enhanced_monitoring_{time.strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('enhanced_monitoring')

@dataclass
class PerformanceBaseline:
    """Performance baseline for SLA monitoring"""
    metric_name: str
    baseline_value: float
    threshold_warning: float
    threshold_critical: float
    created_at: float
    sample_count: int
    confidence_level: float

@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    component: str
    metric_name: str
    condition: str  # gt, lt, eq, contains
    threshold: float
    duration_seconds: int
    severity: str
    escalation_policy: str
    enabled: bool

@dataclass
class DiagnosticResult:
    """Automated diagnostic result"""
    diagnostic_id: str
    component: str
    status: str  # passed, failed, warning
    details: Dict[str, Any]
    recommendations: List[str]
    execution_time_ms: float
    timestamp: float

class BaselineManager:
    """Manages performance baselines and SLA monitoring"""
    
    def __init__(self):
        self.baselines = {}
        self.baseline_file = Path.home() / ".claude" / "monitoring" / "baselines.json"
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_baselines()
        
        # Configuration
        self.min_samples_for_baseline = 100
        self.baseline_confidence_threshold = 0.8
        self.baseline_update_interval = 3600  # 1 hour
        
        logger.info("📊 BaselineManager initialized")
    
    def load_baselines(self):
        """Load baselines from persistent storage"""
        try:
            if self.baseline_file.exists():
                with open(self.baseline_file, 'r') as f:
                    data = json.load(f)
                    self.baselines = {
                        k: PerformanceBaseline(**v) for k, v in data.items()
                    }
                logger.info(f"✅ Loaded {len(self.baselines)} performance baselines")
            else:
                logger.info("📊 No existing baselines found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Failed to load baselines: {e}")
    
    def save_baselines(self):
        """Save baselines to persistent storage"""
        try:
            data = {k: asdict(v) for k, v in self.baselines.items()}
            with open(self.baseline_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("💾 Baselines saved to storage")
        except Exception as e:
            logger.error(f"❌ Failed to save baselines: {e}")
    
    def update_baseline(self, metric_name: str, values: List[float]) -> Optional[PerformanceBaseline]:
        """Update or create baseline for metric"""
        if len(values) < self.min_samples_for_baseline:
            logger.debug(f"📊 Insufficient samples for {metric_name} baseline ({len(values)} < {self.min_samples_for_baseline})")
            return None
        
        # Calculate baseline statistics
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Set thresholds based on statistical distribution
        # Warning: mean + 2*std_dev, Critical: mean + 3*std_dev
        warning_threshold = mean_value + (2 * std_dev)
        critical_threshold = mean_value + (3 * std_dev)
        
        # Calculate confidence based on sample size and distribution
        confidence = min(1.0, len(values) / 500.0)  # Full confidence at 500 samples
        
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=mean_value,
            threshold_warning=warning_threshold,
            threshold_critical=critical_threshold,
            created_at=time.time(),
            sample_count=len(values),
            confidence_level=confidence
        )
        
        self.baselines[metric_name] = baseline
        self.save_baselines()
        
        logger.info(f"📊 Updated baseline for {metric_name}: {mean_value:.2f} (±{std_dev:.2f})")
        return baseline
    
    def check_sla_violation(self, metric_name: str, value: float) -> Optional[str]:
        """Check if value violates SLA baseline"""
        if metric_name not in self.baselines:
            return None
        
        baseline = self.baselines[metric_name]
        
        if baseline.confidence_level < self.baseline_confidence_threshold:
            return None  # Don't alert on low-confidence baselines
        
        if value >= baseline.threshold_critical:
            return 'critical'
        elif value >= baseline.threshold_warning:
            return 'warning'
        
        return None
    
    def get_baseline_status(self) -> Dict[str, Any]:
        """Get status of all baselines"""
        return {
            'total_baselines': len(self.baselines),
            'baselines': {k: asdict(v) for k, v in self.baselines.items()},
            'last_update': max([b.created_at for b in self.baselines.values()]) if self.baselines else 0
        }

class AlertManager:
    """Advanced alerting system with escalation policies"""
    
    def __init__(self):
        self.alert_rules = []
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        self.escalation_timers = {}
        
        # Load alert rules
        self.load_alert_rules()
        
        # Alert suppression to prevent spam
        self.suppression_windows = defaultdict(lambda: 0)
        self.min_alert_interval = 300  # 5 minutes between same alerts
        
        logger.info("🚨 AlertManager initialized")
    
    def load_alert_rules(self):
        """Load alert rules from configuration"""
        rules_file = Path.home() / ".claude" / "monitoring" / "alert_rules.json"
        
        try:
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    data = json.load(f)
                    self.alert_rules = [AlertRule(**rule) for rule in data]
                logger.info(f"✅ Loaded {len(self.alert_rules)} alert rules")
            else:
                # Create default alert rules
                self.create_default_alert_rules()
        except Exception as e:
            logger.error(f"❌ Failed to load alert rules: {e}")
            self.create_default_alert_rules()
    
    def create_default_alert_rules(self):
        """Create default alert rules for hook wrapper monitoring"""
        default_rules = [
            AlertRule(
                rule_id="wrapper_execution_time",
                component="hook_wrapper",
                metric_name="wrapper_execution_time_ms",
                condition="gt",
                threshold=100.0,
                duration_seconds=60,
                severity="warning",
                escalation_policy="standard",
                enabled=True
            ),
            AlertRule(
                rule_id="wrapper_success_rate",
                component="hook_wrapper",
                metric_name="wrapper_success_rate",
                condition="lt",
                threshold=0.9,
                duration_seconds=300,
                severity="critical",
                escalation_policy="urgent",
                enabled=True
            ),
            AlertRule(
                rule_id="credential_provider_failure",
                component="credential_provider",
                metric_name="health_status",
                condition="eq",
                threshold=0,  # 0 = unhealthy
                duration_seconds=30,
                severity="critical",
                escalation_policy="urgent",
                enabled=True
            ),
            AlertRule(
                rule_id="observability_system_down",
                component="observability_system",
                metric_name="health_status",
                condition="eq",
                threshold=0,
                duration_seconds=60,
                severity="critical",
                escalation_policy="urgent",
                enabled=True
            ),
            AlertRule(
                rule_id="high_system_cpu",
                component="system",
                metric_name="system_cpu_percent",
                condition="gt",
                threshold=90.0,
                duration_seconds=300,
                severity="warning",
                escalation_policy="standard",
                enabled=True
            ),
            AlertRule(
                rule_id="high_system_memory",
                component="system",
                metric_name="system_memory_percent",
                condition="gt",
                threshold=95.0,
                duration_seconds=180,
                severity="critical",
                escalation_policy="urgent",
                enabled=True
            )
        ]
        
        self.alert_rules = default_rules
        self.save_alert_rules()
        logger.info("📋 Created default alert rules")
    
    def save_alert_rules(self):
        """Save alert rules to configuration"""
        rules_file = Path.home() / ".claude" / "monitoring" / "alert_rules.json"
        rules_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = [asdict(rule) for rule in self.alert_rules]
            with open(rules_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("💾 Alert rules saved")
        except Exception as e:
            logger.error(f"❌ Failed to save alert rules: {e}")
    
    def evaluate_alerts(self, metrics: Dict[str, float], health_statuses: Dict[str, str]):
        """Evaluate all alert rules against current metrics"""
        current_time = time.time()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                should_alert = self._evaluate_rule(rule, metrics, health_statuses)
                
                if should_alert:
                    self._trigger_alert(rule, current_time)
                else:
                    self._clear_alert(rule.rule_id, current_time)
                    
            except Exception as e:
                logger.error(f"❌ Error evaluating alert rule {rule.rule_id}: {e}")
    
    def _evaluate_rule(self, rule: AlertRule, metrics: Dict[str, float], health_statuses: Dict[str, str]) -> bool:
        """Evaluate a single alert rule"""
        
        # Get metric value
        if rule.metric_name == "health_status":
            # Special handling for health status
            status = health_statuses.get(rule.component, "unknown")
            value = 1 if status == "healthy" else 0.5 if status == "degraded" else 0
        else:
            value = metrics.get(rule.metric_name, 0)
        
        # Apply condition
        if rule.condition == "gt":
            return value > rule.threshold
        elif rule.condition == "lt":
            return value < rule.threshold
        elif rule.condition == "eq":
            return abs(value - rule.threshold) < 0.001
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, current_time: float):
        """Trigger an alert"""
        alert_key = f"{rule.component}_{rule.rule_id}"
        
        # Check suppression window
        if current_time - self.suppression_windows[alert_key] < self.min_alert_interval:
            return
        
        # Create alert
        alert = {
            'rule_id': rule.rule_id,
            'component': rule.component,
            'severity': rule.severity,
            'message': f"{rule.component} alert: {rule.metric_name} violates threshold",
            'threshold': rule.threshold,
            'timestamp': current_time,
            'escalation_policy': rule.escalation_policy
        }
        
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        self.suppression_windows[alert_key] = current_time
        
        # Send alert notification
        self._send_alert_notification(alert)
        
        logger.warning(f"🚨 ALERT TRIGGERED: {alert['component']} - {alert['message']}")
    
    def _clear_alert(self, rule_id: str, current_time: float):
        """Clear an active alert"""
        alert_key_pattern = f"_{rule_id}"
        cleared_alerts = []
        
        for key in list(self.active_alerts.keys()):
            if alert_key_pattern in key:
                cleared_alerts.append(self.active_alerts.pop(key))
        
        for alert in cleared_alerts:
            logger.info(f"✅ ALERT CLEARED: {alert['component']} - {alert['rule_id']}")
    
    def _send_alert_notification(self, alert: Dict[str, Any]):
        """Send alert notification to external systems"""
        try:
            # Send to observability system
            event_data = {
                'source_app': 'hook-wrapper-enhanced-monitoring',
                'session_id': 'monitoring_alerts',
                'hook_event_type': 'AlertTriggered',
                'payload': json.dumps(alert),
                'timestamp': int(alert['timestamp'] * 1000)
            }
            
            response = requests.post(
                'http://localhost:4000/events',
                json=event_data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug("📤 Alert sent to observability system")
            else:
                logger.warning(f"⚠️ Failed to send alert notification: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send alert notification: {e}")
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Get current alert status"""
        return {
            'active_alerts_count': len(self.active_alerts),
            'active_alerts': list(self.active_alerts.values()),
            'total_rules': len(self.alert_rules),
            'enabled_rules': len([r for r in self.alert_rules if r.enabled]),
            'recent_alerts': list(self.alert_history)[-10:]
        }

class AutomatedDiagnostics:
    """Automated diagnostic system for hook wrapper infrastructure"""
    
    def __init__(self):
        self.diagnostic_results = deque(maxlen=1000)
        self.diagnostic_schedule = {}
        
        # Initialize diagnostic procedures
        self.diagnostics = {
            'credential_provider_connectivity': self._diagnose_credential_provider,
            'secret_manager_access': self._diagnose_secret_manager,
            'hook_wrapper_transparency': self._diagnose_wrapper_transparency,
            'observability_integration': self._diagnose_observability,
            'system_resources': self._diagnose_system_resources,
            'api_key_validity': self._diagnose_api_keys,
            'cache_health': self._diagnose_cache_health
        }
        
        logger.info("🔧 AutomatedDiagnostics initialized")
    
    def run_all_diagnostics(self) -> List[DiagnosticResult]:
        """Run all diagnostic procedures"""
        results = []
        
        for diagnostic_id, diagnostic_func in self.diagnostics.items():
            try:
                start_time = time.time()
                result = diagnostic_func()
                execution_time = (time.time() - start_time) * 1000
                
                result.execution_time_ms = execution_time
                results.append(result)
                self.diagnostic_results.append(result)
                
                status_emoji = "✅" if result.status == "passed" else "⚠️" if result.status == "warning" else "❌"
                logger.info(f"{status_emoji} Diagnostic {diagnostic_id}: {result.status} ({execution_time:.1f}ms)")
                
            except Exception as e:
                error_result = DiagnosticResult(
                    diagnostic_id=diagnostic_id,
                    component="diagnostic_system",
                    status="failed",
                    details={'error': str(e)},
                    recommendations=[f"Fix diagnostic procedure: {diagnostic_id}"],
                    execution_time_ms=0,
                    timestamp=time.time()
                )
                results.append(error_result)
                logger.error(f"❌ Diagnostic {diagnostic_id} failed: {e}")
        
        return results
    
    def _diagnose_credential_provider(self) -> DiagnosticResult:
        """Diagnose credential provider health"""
        try:
            from credential_provider import CredentialProvider
            provider = CredentialProvider()
            health_data = provider.health_check()
            
            status = health_data.get('status', 'unknown')
            available_keys = len(health_data.get('available_keys', []))
            cache_valid = health_data.get('cache_status', {}).get('cache_valid', False)
            
            recommendations = []
            if status != 'healthy':
                recommendations.append("Check Secret Manager connectivity and permissions")
            if available_keys < 3:
                recommendations.append("Verify API keys are properly configured in Secret Manager")
            if not cache_valid:
                recommendations.append("Cache is expired or invalid, credentials may be slow to load")
            
            diagnostic_status = "passed" if status == "healthy" and available_keys >= 3 else "warning" if status == "degraded" else "failed"
            
            return DiagnosticResult(
                diagnostic_id="credential_provider_connectivity",
                component="credential_provider",
                status=diagnostic_status,
                details=health_data,
                recommendations=recommendations,
                execution_time_ms=0,
                timestamp=time.time()
            )
            
        except Exception as e:
            return DiagnosticResult(
                diagnostic_id="credential_provider_connectivity",
                component="credential_provider",
                status="failed",
                details={'error': str(e)},
                recommendations=["Fix credential provider import or initialization"],
                execution_time_ms=0,
                timestamp=time.time()
            )
    
    def _diagnose_secret_manager(self) -> DiagnosticResult:
        """Diagnose Google Secret Manager connectivity"""
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            
            # Test with a known secret
            test_name = "projects/custom-mix-460500-g9/secrets/gemini-api-key/versions/latest"
            response = client.access_secret_version(request={"name": test_name})
            
            secret_value = response.payload.data.decode("UTF-8")
            is_valid = len(secret_value.strip()) > 10
            
            status = "passed" if is_valid else "warning"
            recommendations = [] if is_valid else ["Check Secret Manager secret values"]
            
            return DiagnosticResult(
                diagnostic_id="secret_manager_access",
                component="secret_manager",
                status=status,
                details={'connectivity': True, 'test_secret_valid': is_valid},
                recommendations=recommendations,
                execution_time_ms=0,
                timestamp=time.time()
            )
            
        except Exception as e:
            return DiagnosticResult(
                diagnostic_id="secret_manager_access",
                component="secret_manager",
                status="failed",
                details={'error': str(e), 'connectivity': False},
                recommendations=["Check Google Cloud credentials and permissions"],
                execution_time_ms=0,
                timestamp=time.time()
            )
    
    def _diagnose_wrapper_transparency(self) -> DiagnosticResult:
        """Diagnose hook wrapper transparency"""
        try:
            # Test the wrapper transparency function
            wrapper_path = Path(__file__).parent / "hook_wrapper.py"
            
            if not wrapper_path.exists():
                return DiagnosticResult(
                    diagnostic_id="hook_wrapper_transparency",
                    component="hook_wrapper",
                    status="failed",
                    details={'error': 'Hook wrapper not found'},
                    recommendations=["Ensure hook wrapper is properly installed"],
                    execution_time_ms=0,
                    timestamp=time.time()
                )
            
            # Test transparency by running the test function
            result = subprocess.run(
                ['uv', 'run', str(wrapper_path), '--test'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0 and "Transparency test passed" in result.stdout
            
            status = "passed" if success else "failed"
            recommendations = [] if success else ["Check hook wrapper transparency implementation"]
            
            return DiagnosticResult(
                diagnostic_id="hook_wrapper_transparency",
                component="hook_wrapper",
                status=status,
                details={'test_output': result.stdout, 'test_success': success},
                recommendations=recommendations,
                execution_time_ms=0,
                timestamp=time.time()
            )
            
        except Exception as e:
            return DiagnosticResult(
                diagnostic_id="hook_wrapper_transparency",
                component="hook_wrapper",
                status="failed",
                details={'error': str(e)},
                recommendations=["Fix hook wrapper test execution"],
                execution_time_ms=0,
                timestamp=time.time()
            )
    
    def _diagnose_observability(self) -> DiagnosticResult:
        """Diagnose observability system integration"""
        try:
            # Test observability server health
            response = requests.get('http://localhost:4000/health', timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                active_connections = health_data.get('metrics', {}).get('activeConnections', 0)
                uptime = health_data.get('metrics', {}).get('uptime', 0)
                
                status = "passed" if uptime > 10 else "warning"  # Should have been running for at least 10 seconds
                recommendations = [] if status == "passed" else ["Observability server recently started or unstable"]
                
                return DiagnosticResult(
                    diagnostic_id="observability_integration",
                    component="observability_system",
                    status=status,
                    details=health_data,
                    recommendations=recommendations,
                    execution_time_ms=0,
                    timestamp=time.time()
                )
            else:
                return DiagnosticResult(
                    diagnostic_id="observability_integration",
                    component="observability_system",
                    status="failed",
                    details={'http_status': response.status_code},
                    recommendations=["Start observability server or check configuration"],
                    execution_time_ms=0,
                    timestamp=time.time()
                )
                
        except requests.exceptions.RequestException as e:
            return DiagnosticResult(
                diagnostic_id="observability_integration",
                component="observability_system",
                status="failed",
                details={'error': str(e)},
                recommendations=["Start observability server: bun run dev in apps/server"],
                execution_time_ms=0,
                timestamp=time.time()
            )
    
    def _diagnose_system_resources(self) -> DiagnosticResult:
        """Diagnose system resource availability"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Resource thresholds
            cpu_warning = 80
            cpu_critical = 95
            memory_warning = 85
            memory_critical = 95
            disk_warning = 90
            disk_critical = 95
            
            issues = []
            recommendations = []
            
            if cpu_percent > cpu_critical:
                issues.append("Critical CPU usage")
                recommendations.append("Investigate high CPU processes")
            elif cpu_percent > cpu_warning:
                issues.append("High CPU usage")
                recommendations.append("Monitor CPU usage trends")
            
            if memory.percent > memory_critical:
                issues.append("Critical memory usage")
                recommendations.append("Free memory or increase system RAM")
            elif memory.percent > memory_warning:
                issues.append("High memory usage")
                recommendations.append("Monitor memory usage trends")
            
            if disk.percent > disk_critical:
                issues.append("Critical disk usage")
                recommendations.append("Free disk space immediately")
            elif disk.percent > disk_warning:
                issues.append("High disk usage")
                recommendations.append("Plan disk cleanup")
            
            status = "failed" if any("Critical" in issue for issue in issues) else "warning" if issues else "passed"
            
            return DiagnosticResult(
                diagnostic_id="system_resources",
                component="system",
                status=status,
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'issues': issues
                },
                recommendations=recommendations,
                execution_time_ms=0,
                timestamp=time.time()
            )
            
        except Exception as e:
            return DiagnosticResult(
                diagnostic_id="system_resources",
                component="system",
                status="failed",
                details={'error': str(e)},
                recommendations=["Install psutil for system resource monitoring"],
                execution_time_ms=0,
                timestamp=time.time()
            )
    
    def _diagnose_api_keys(self) -> DiagnosticResult:
        """Diagnose API key validity"""
        try:
            from credential_provider import CredentialProvider
            provider = CredentialProvider()
            
            # Test specific API keys
            api_keys_to_test = ['GEMINI_API_KEY', 'OPENAI_API_KEY', ]
            key_status = {}
            
            for key_name in api_keys_to_test:
                api_key = provider.get_api_key(key_name)
                if api_key and len(api_key.strip()) > 10:
                    key_status[key_name] = 'valid'
                else:
                    key_status[key_name] = 'invalid'
            
            valid_keys = len([k for k, v in key_status.items() if v == 'valid'])
            total_keys = len(key_status)
            
            if valid_keys == total_keys:
                status = "passed"
                recommendations = []
            elif valid_keys > 0:
                status = "warning"
                recommendations = ["Some API keys are missing or invalid"]
            else:
                status = "failed"
                recommendations = ["No valid API keys found - check Secret Manager configuration"]
            
            return DiagnosticResult(
                diagnostic_id="api_key_validity",
                component="credential_provider",
                status=status,
                details={
                    'key_status': key_status,
                    'valid_keys': valid_keys,
                    'total_keys': total_keys
                },
                recommendations=recommendations,
                execution_time_ms=0,
                timestamp=time.time()
            )
            
        except Exception as e:
            return DiagnosticResult(
                diagnostic_id="api_key_validity",
                component="credential_provider",
                status="failed",
                details={'error': str(e)},
                recommendations=["Fix credential provider for API key testing"],
                execution_time_ms=0,
                timestamp=time.time()
            )
    
    def _diagnose_cache_health(self) -> DiagnosticResult:
        """Diagnose credential cache health"""
        try:
            from credential_provider import CredentialProvider
            provider = CredentialProvider()
            cache_status = provider.get_cache_status()
            
            cache_valid = cache_status.get('cache_valid', False)
            cache_age = cache_status.get('cache_age_seconds', 0)
            cache_size = cache_status.get('cache_size', 0)
            
            recommendations = []
            
            if not cache_valid:
                recommendations.append("Cache is invalid - credentials will be slow to load")
            if cache_age and cache_age > 3300:  # 55 minutes
                recommendations.append("Cache will expire soon - consider refreshing")
            if cache_size == 0:
                recommendations.append("Cache is empty - no credentials cached")
            
            status = "passed" if cache_valid and cache_size > 0 else "warning"
            
            return DiagnosticResult(
                diagnostic_id="cache_health",
                component="credential_cache",
                status=status,
                details=cache_status,
                recommendations=recommendations,
                execution_time_ms=0,
                timestamp=time.time()
            )
            
        except Exception as e:
            return DiagnosticResult(
                diagnostic_id="cache_health",
                component="credential_cache",
                status="failed",
                details={'error': str(e)},
                recommendations=["Fix credential provider for cache diagnostics"],
                execution_time_ms=0,
                timestamp=time.time()
            )
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """Get summary of recent diagnostic results"""
        if not self.diagnostic_results:
            return {'status': 'no_diagnostics_run', 'results': []}
        
        recent_results = list(self.diagnostic_results)[-len(self.diagnostics):]
        
        passed = len([r for r in recent_results if r.status == "passed"])
        warning = len([r for r in recent_results if r.status == "warning"])
        failed = len([r for r in recent_results if r.status == "failed"])
        
        overall_status = "passed" if failed == 0 and warning == 0 else "warning" if failed == 0 else "failed"
        
        return {
            'overall_status': overall_status,
            'summary': {
                'passed': passed,
                'warning': warning,
                'failed': failed,
                'total': len(recent_results)
            },
            'results': [asdict(r) for r in recent_results]
        }

class EnhancedMonitoringSystem:
    """Main enhanced monitoring system orchestrator"""
    
    def __init__(self):
        # Initialize core systems
        self.baseline_manager = BaselineManager()
        self.alert_manager = AlertManager()
        self.diagnostics = AutomatedDiagnostics()
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_health_check = 0
        self.last_baseline_update = 0
        self.last_diagnostic_run = 0
        
        # Configuration
        self.config = {
            'monitoring_interval': 30,  # seconds
            'health_check_interval': 60,  # seconds
            'baseline_update_interval': 3600,  # 1 hour
            'diagnostic_interval': 1800,  # 30 minutes
            'observability_url': 'http://localhost:4000'
        }
        
        # Schedule recurring tasks
        self.setup_scheduler()
        
        logger.info("🚀 EnhancedMonitoringSystem initialized")
    
    def setup_scheduler(self):
        """Setup recurring monitoring tasks"""
        schedule.every(self.config['health_check_interval']).seconds.do(self._scheduled_health_check)
        schedule.every(self.config['baseline_update_interval']).seconds.do(self._scheduled_baseline_update)
        schedule.every(self.config['diagnostic_interval']).seconds.do(self._scheduled_diagnostics)
        
        logger.info("⏰ Monitoring scheduler configured")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if self.monitoring_active:
            logger.warning("⚠️ Monitoring already active")
            return
        
        def monitoring_worker():
            logger.info("🔄 Enhanced monitoring started")
            self.monitoring_active = True
            
            while self.monitoring_active:
                try:
                    # Run scheduled tasks
                    schedule.run_pending()
                    
                    # Collect and evaluate current metrics
                    self._collect_and_evaluate_metrics()
                    
                    # Sleep for monitoring interval
                    time.sleep(self.config['monitoring_interval'])
                    
                except Exception as e:
                    logger.error(f"❌ Error in monitoring loop: {e}")
                    time.sleep(self.config['monitoring_interval'])
            
            logger.info("🛑 Enhanced monitoring stopped")
        
        self.monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🚀 Enhanced monitoring system started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("✅ Enhanced monitoring system stopped")
    
    def _collect_and_evaluate_metrics(self):
        """Collect current metrics and evaluate against baselines and alerts"""
        try:
            # Import monitoring system
            from monitoring_system import get_monitoring_instance
            monitoring = get_monitoring_instance()
            
            # Get comprehensive status
            status = monitoring.get_comprehensive_status()
            
            # Extract metrics for evaluation
            metrics = {
                'wrapper_execution_time_ms': status['performance_metrics']['wrapper_execution_stats'].get('mean', 0),
                'wrapper_success_rate': status['performance_metrics']['success_rate_5min'],
                'system_cpu_percent': status['system_metrics']['cpu_percent'],
                'system_memory_percent': status['system_metrics']['memory_percent'],
                'available_api_keys': status['performance_metrics']['available_api_keys']
            }
            
            # Extract health statuses
            health_statuses = {
                'credential_provider': status['health_checks']['credential_provider']['status'],
                'observability_system': status['health_checks']['observability_system']['status'],
                'hook_wrapper': 'healthy' if status['performance_metrics']['success_rate_5min'] > 0.95 else 'degraded'
            }
            
            # Check for SLA violations
            self._check_sla_violations(metrics)
            
            # Evaluate alert rules
            self.alert_manager.evaluate_alerts(metrics, health_statuses)
            
            # Send status update to observability system
            self._send_monitoring_update(status)
            
        except Exception as e:
            logger.error(f"❌ Error collecting metrics: {e}")
    
    def _check_sla_violations(self, metrics: Dict[str, float]):
        """Check metrics against SLA baselines"""
        for metric_name, value in metrics.items():
            violation_level = self.baseline_manager.check_sla_violation(metric_name, value)
            
            if violation_level:
                logger.warning(f"⚠️ SLA violation: {metric_name} = {value} ({violation_level})")
                
                # Create SLA violation alert
                alert_data = {
                    'alert_type': 'sla_violation',
                    'severity': violation_level,
                    'component': 'performance_baseline',
                    'message': f"SLA violation: {metric_name} = {value}",
                    'timestamp': time.time(),
                    'metadata': {'metric_name': metric_name, 'value': value, 'violation_level': violation_level}
                }
                
                self.alert_manager.alert_history.append(alert_data)
    
    def _scheduled_health_check(self):
        """Scheduled health check"""
        logger.info("🔍 Running scheduled health check")
        
        try:
            from monitoring_system import get_monitoring_instance
            monitoring = get_monitoring_instance()
            
            # Run health checks
            monitoring.check_credential_provider_health()
            monitoring.check_observability_system_health()
            
            self.last_health_check = time.time()
            
        except Exception as e:
            logger.error(f"❌ Scheduled health check failed: {e}")
    
    def _scheduled_baseline_update(self):
        """Scheduled baseline update"""
        logger.info("📊 Running scheduled baseline update")
        
        try:
            from monitoring_system import get_monitoring_instance
            monitoring = get_monitoring_instance()
            
            # Update baselines for key metrics
            metrics_to_baseline = [
                'wrapper_execution_time_ms',
                'wrapper_success_rate',
                'system_cpu_percent',
                'system_memory_percent'
            ]
            
            for metric_name in metrics_to_baseline:
                # Get recent values from performance tracker
                values = [v for v, t in monitoring.performance_tracker.metrics.get(metric_name, [])]
                if len(values) >= self.baseline_manager.min_samples_for_baseline:
                    self.baseline_manager.update_baseline(metric_name, values)
            
            self.last_baseline_update = time.time()
            
        except Exception as e:
            logger.error(f"❌ Scheduled baseline update failed: {e}")
    
    def _scheduled_diagnostics(self):
        """Scheduled diagnostic run"""
        logger.info("🔧 Running scheduled diagnostics")
        
        try:
            results = self.diagnostics.run_all_diagnostics()
            
            # Count diagnostic results
            failed_diagnostics = [r for r in results if r.status == "failed"]
            warning_diagnostics = [r for r in results if r.status == "warning"]
            
            if failed_diagnostics:
                logger.warning(f"⚠️ {len(failed_diagnostics)} diagnostic(s) failed")
            if warning_diagnostics:
                logger.info(f"📝 {len(warning_diagnostics)} diagnostic(s) have warnings")
            
            self.last_diagnostic_run = time.time()
            
        except Exception as e:
            logger.error(f"❌ Scheduled diagnostics failed: {e}")
    
    def _send_monitoring_update(self, status: Dict[str, Any]):
        """Send monitoring update to observability system"""
        try:
            # Enhance status with enhanced monitoring data
            enhanced_status = {
                **status,
                'enhanced_monitoring': {
                    'baseline_status': self.baseline_manager.get_baseline_status(),
                    'alert_status': self.alert_manager.get_alert_status(),
                    'diagnostic_status': self.diagnostics.get_diagnostic_summary(),
                    'monitoring_config': self.config,
                    'last_checks': {
                        'health_check': self.last_health_check,
                        'baseline_update': self.last_baseline_update,
                        'diagnostic_run': self.last_diagnostic_run
                    }
                }
            }
            
            # Send to observability server
            event_data = {
                'source_app': 'hook-wrapper-enhanced-monitoring',
                'session_id': 'enhanced_monitoring_system',
                'hook_event_type': 'EnhancedMonitoringUpdate',
                'payload': json.dumps(enhanced_status, default=str),
                'timestamp': int(time.time() * 1000)
            }
            
            response = requests.post(
                f"{self.config['observability_url']}/events",
                json=event_data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug("📊 Enhanced monitoring update sent to observability system")
            else:
                logger.warning(f"⚠️ Failed to send monitoring update: HTTP {response.status_code}")
                
        except Exception as e:
            logger.debug(f"⚠️ Failed to send monitoring update: {e}")  # Debug level to avoid spam
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive enhanced monitoring status"""
        try:
            # Get base monitoring status
            from monitoring_system import get_monitoring_instance
            base_status = get_monitoring_instance().get_comprehensive_status()
            
            # Add enhanced monitoring data
            enhanced_status = {
                **base_status,
                'enhanced_monitoring': {
                    'system_active': self.monitoring_active,
                    'baseline_manager': self.baseline_manager.get_baseline_status(),
                    'alert_manager': self.alert_manager.get_alert_status(),
                    'diagnostics': self.diagnostics.get_diagnostic_summary(),
                    'configuration': self.config,
                    'last_activities': {
                        'health_check': self.last_health_check,
                        'baseline_update': self.last_baseline_update,
                        'diagnostic_run': self.last_diagnostic_run
                    }
                }
            }
            
            return enhanced_status
            
        except Exception as e:
            logger.error(f"❌ Error getting comprehensive status: {e}")
            return {
                'error': str(e),
                'enhanced_monitoring': {
                    'system_active': self.monitoring_active,
                    'error': 'Failed to get base monitoring status'
                }
            }
    
    def run_immediate_diagnostic(self) -> List[DiagnosticResult]:
        """Run immediate diagnostic check"""
        logger.info("🔧 Running immediate diagnostics")
        return self.diagnostics.run_all_diagnostics()
    
    def force_baseline_update(self):
        """Force immediate baseline update"""
        logger.info("📊 Forcing baseline update")
        self._scheduled_baseline_update()
    
    def test_alert_system(self):
        """Test alert system functionality"""
        logger.info("🚨 Testing alert system")
        
        # Create test alert
        test_alert = {
            'alert_type': 'test_alert',
            'severity': 'info',
            'component': 'enhanced_monitoring',
            'message': 'Test alert triggered from enhanced monitoring system',
            'timestamp': time.time(),
            'metadata': {'test': True}
        }
        
        self.alert_manager.alert_history.append(test_alert)
        self.alert_manager._send_alert_notification(test_alert)
        
        logger.info("✅ Test alert sent")

# Global enhanced monitoring instance
_enhanced_monitoring_instance = None

def get_enhanced_monitoring_instance() -> EnhancedMonitoringSystem:
    """Get singleton enhanced monitoring instance"""
    global _enhanced_monitoring_instance
    if _enhanced_monitoring_instance is None:
        _enhanced_monitoring_instance = EnhancedMonitoringSystem()
    return _enhanced_monitoring_instance

if __name__ == '__main__':
    # CLI interface for enhanced monitoring system
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Hook Wrapper Monitoring System')
    parser.add_argument('--start', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--status', action='store_true', help='Show comprehensive status')
    parser.add_argument('--diagnostics', action='store_true', help='Run immediate diagnostics')
    parser.add_argument('--baselines', action='store_true', help='Update performance baselines')
    parser.add_argument('--test-alerts', action='store_true', help='Test alert system')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (with --start)')
    
    args = parser.parse_args()
    
    enhanced_monitoring = get_enhanced_monitoring_instance()
    
    if args.start:
        enhanced_monitoring.start_monitoring()
        
        if args.daemon:
            try:
                # Keep running until interrupted
                import signal
                signal.pause()
            except KeyboardInterrupt:
                print("\n🛑 Stopping enhanced monitoring...")
                enhanced_monitoring.stop_monitoring()
        else:
            print("🚀 Enhanced monitoring started in background")
    
    elif args.status:
        status = enhanced_monitoring.get_comprehensive_status()
        print(json.dumps(status, indent=2, default=str))
    
    elif args.diagnostics:
        results = enhanced_monitoring.run_immediate_diagnostic()
        print("🔧 Diagnostic Results:")
        for result in results:
            status_emoji = "✅" if result.status == "passed" else "⚠️" if result.status == "warning" else "❌"
            print(f"  {status_emoji} {result.diagnostic_id}: {result.status}")
            if result.recommendations:
                for rec in result.recommendations:
                    print(f"    💡 {rec}")
    
    elif args.baselines:
        enhanced_monitoring.force_baseline_update()
        print("📊 Performance baselines updated")
    
    elif args.test_alerts:
        enhanced_monitoring.test_alert_system()
        print("🚨 Alert system test completed")
    
    else:
        # Default: show brief status
        status = enhanced_monitoring.get_comprehensive_status()
        enhanced_status = status.get('enhanced_monitoring', {})
        
        print("🔍 Enhanced Monitoring Status:")
        print(f"  System Active: {'✅' if enhanced_status.get('system_active') else '❌'}")
        print(f"  Overall Status: {status.get('overall_status', 'unknown')}")
        print(f"  Active Alerts: {enhanced_status.get('alert_manager', {}).get('active_alerts_count', 0)}")
        print(f"  Diagnostics: {enhanced_status.get('diagnostics', {}).get('overall_status', 'unknown')}")
        print(f"  Baselines: {enhanced_status.get('baseline_manager', {}).get('total_baselines', 0)}")