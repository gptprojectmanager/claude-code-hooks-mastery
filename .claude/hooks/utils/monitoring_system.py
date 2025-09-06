#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
#     "psutil",
#     "requests",
# ]
# ///

"""
Comprehensive Monitoring System for Hook Wrapper Infrastructure
==============================================================

This module provides real-time monitoring, health checks, and telemetry
for the hook wrapper system including credential provider health,
wrapper performance, and observability system integration.

Key Features:
- Real-time performance metrics collection
- Credential provider health monitoring  
- API key usage pattern tracking
- Observability system integration health
- Automated alerting for failures
- Performance baselines and SLA monitoring
- Structured logging for debugging

Architecture:
- MonitoringCollector: Collects metrics and health data
- HealthChecker: Validates system components
- AlertManager: Handles failure notifications
- MetricsExporter: Sends data to observability system
- DashboardIntegration: Provides monitoring UI data
"""

import os
import sys
import time
import json
import logging
import threading
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import requests

# Setup logging for monitoring system
log_dir = Path.home() / ".claude" / "logs" / "monitoring"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"monitoring_{time.strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('monitoring_system')

@dataclass
class MetricData:
    """Individual metric data point"""
    metric_name: str
    value: float
    timestamp: float
    tags: Dict[str, str]
    unit: str = "count"

@dataclass
class HealthStatus:
    """Health check result"""
    component: str
    status: str  # healthy, degraded, unhealthy
    details: Dict[str, Any]
    timestamp: float
    latency_ms: Optional[float] = None

@dataclass
class AlertEvent:
    """Alert notification data"""
    alert_type: str
    severity: str  # critical, warning, info
    component: str
    message: str
    timestamp: float
    metadata: Dict[str, Any]

class PerformanceTracker:
    """Tracks performance metrics with rolling windows"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.lock = threading.Lock()
    
    def record_metric(self, metric_name: str, value: float, timestamp: float = None):
        """Record a performance metric"""
        if timestamp is None:
            timestamp = time.time()
        
        with self.lock:
            self.metrics[metric_name].append((value, timestamp))
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistical analysis of metric"""
        with self.lock:
            values = [v for v, t in self.metrics[metric_name]]
            
            if not values:
                return {}
            
            return {
                'count': len(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'p95': sorted(values)[int(len(values) * 0.95)] if len(values) > 0 else 0,
                'p99': sorted(values)[int(len(values) * 0.99)] if len(values) > 0 else 0
            }
    
    def get_recent_average(self, metric_name: str, seconds: int = 60) -> float:
        """Get average of recent metrics within time window"""
        cutoff = time.time() - seconds
        with self.lock:
            recent_values = [v for v, t in self.metrics[metric_name] if t >= cutoff]
            return statistics.mean(recent_values) if recent_values else 0.0

class MonitoringCollector:
    """Main monitoring system that collects all metrics and health data"""
    
    def __init__(self):
        self.performance_tracker = PerformanceTracker()
        self.health_checks = {}
        self.alert_history = deque(maxlen=1000)
        self.start_time = time.time()
        
        # Monitoring configuration
        self.config = {
            'health_check_interval': 30,  # seconds
            'metric_collection_interval': 10,  # seconds
            'performance_threshold_ms': 50,  # wrapper should execute under 50ms
            'credential_cache_ttl_warning': 3300,  # warn if cache expires soon (55 min)
            'observability_timeout': 5,  # seconds for observability health checks
        }
        
        logger.info("🔍 MonitoringCollector initialized")
    
    def collect_wrapper_metrics(self, execution_time: float, hook_name: str, 
                               success: bool, credentials_loaded: int) -> MetricData:
        """Collect metrics from hook wrapper execution"""
        
        # Record performance metrics
        self.performance_tracker.record_metric('wrapper_execution_time_ms', execution_time * 1000)
        self.performance_tracker.record_metric('credentials_loaded_count', credentials_loaded)
        
        # Track success/failure rates
        success_value = 1.0 if success else 0.0
        self.performance_tracker.record_metric('wrapper_success_rate', success_value)
        self.performance_tracker.record_metric(f'hook_{hook_name}_success_rate', success_value)
        
        # Create metric data
        metric = MetricData(
            metric_name='hook_wrapper_execution',
            value=execution_time * 1000,  # Convert to milliseconds
            timestamp=time.time(),
            tags={
                'hook_name': hook_name,
                'success': str(success),
                'credentials_loaded': str(credentials_loaded)
            },
            unit='milliseconds'
        )
        
        # Check performance threshold
        if execution_time * 1000 > self.config['performance_threshold_ms']:
            self._generate_alert(AlertEvent(
                alert_type='performance_degradation',
                severity='warning',
                component='hook_wrapper',
                message=f"Hook wrapper execution time ({execution_time*1000:.1f}ms) exceeded threshold ({self.config['performance_threshold_ms']}ms) for {hook_name}",
                timestamp=time.time(),
                metadata={'execution_time_ms': execution_time * 1000, 'hook_name': hook_name}
            ))
        
        logger.debug(f"📊 Collected wrapper metrics: {hook_name} - {execution_time*1000:.1f}ms - Success: {success}")
        return metric
    
    def check_credential_provider_health(self) -> HealthStatus:
        """Comprehensive health check for credential provider"""
        start_time = time.time()
        
        try:
            # Import credential provider
            from credential_provider import CredentialProvider
            provider = CredentialProvider()
            
            # Run health check
            health_data = provider.health_check()
            latency_ms = (time.time() - start_time) * 1000
            
            # Determine overall status
            status = health_data.get('status', 'unknown')
            if status == 'healthy':
                status_level = 'healthy'
            elif status == 'degraded':
                status_level = 'degraded'
            else:
                status_level = 'unhealthy'
            
            # Check cache health
            cache_status = health_data.get('cache_status', {})
            cache_age = cache_status.get('cache_age_seconds', 0)
            
            if cache_age and cache_age > self.config['credential_cache_ttl_warning']:
                self._generate_alert(AlertEvent(
                    alert_type='cache_expiry_warning',
                    severity='warning',
                    component='credential_provider',
                    message=f"Credential cache will expire soon (age: {cache_age:.0f}s)",
                    timestamp=time.time(),
                    metadata={'cache_age_seconds': cache_age}
                ))
            
            # Track API key availability
            available_keys = len(health_data.get('available_keys', []))
            self.performance_tracker.record_metric('available_api_keys_count', available_keys)
            
            health_status = HealthStatus(
                component='credential_provider',
                status=status_level,
                details=health_data,
                timestamp=time.time(),
                latency_ms=latency_ms
            )
            
            self.health_checks['credential_provider'] = health_status
            logger.debug(f"✅ Credential provider health: {status_level} ({latency_ms:.1f}ms)")
            
            return health_status
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            health_status = HealthStatus(
                component='credential_provider',
                status='unhealthy',
                details={'error': str(e), 'error_type': type(e).__name__},
                timestamp=time.time(),
                latency_ms=latency_ms
            )
            
            self._generate_alert(AlertEvent(
                alert_type='credential_provider_failure',
                severity='critical',
                component='credential_provider',
                message=f"Credential provider health check failed: {e}",
                timestamp=time.time(),
                metadata={'error': str(e), 'latency_ms': latency_ms}
            ))
            
            self.health_checks['credential_provider'] = health_status
            logger.error(f"❌ Credential provider health check failed: {e}")
            
            return health_status
    
    def check_observability_system_health(self) -> HealthStatus:
        """Check health of observability system integration"""
        start_time = time.time()
        
        try:
            # Test server health endpoint
            response = requests.get(
                'http://localhost:4000/health',
                timeout=self.config['observability_timeout']
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                
                health_status = HealthStatus(
                    component='observability_system',
                    status='healthy',
                    details=health_data,
                    timestamp=time.time(),
                    latency_ms=latency_ms
                )
                
                # Track observability metrics
                metrics = health_data.get('metrics', {})
                if 'activeConnections' in metrics:
                    self.performance_tracker.record_metric('observability_active_connections', metrics['activeConnections'])
                if 'uptime' in metrics:
                    self.performance_tracker.record_metric('observability_uptime_seconds', metrics['uptime'])
                
                logger.debug(f"✅ Observability system health: healthy ({latency_ms:.1f}ms)")
                
            else:
                health_status = HealthStatus(
                    component='observability_system',
                    status='degraded',
                    details={'http_status': response.status_code, 'response': response.text[:200]},
                    timestamp=time.time(),
                    latency_ms=latency_ms
                )
                
                self._generate_alert(AlertEvent(
                    alert_type='observability_system_degraded',
                    severity='warning',
                    component='observability_system',
                    message=f"Observability system returned HTTP {response.status_code}",
                    timestamp=time.time(),
                    metadata={'http_status': response.status_code, 'latency_ms': latency_ms}
                ))
                
                logger.warning(f"⚠️ Observability system degraded: HTTP {response.status_code}")
            
            self.health_checks['observability_system'] = health_status
            return health_status
            
        except requests.exceptions.RequestException as e:
            latency_ms = (time.time() - start_time) * 1000
            
            health_status = HealthStatus(
                component='observability_system',
                status='unhealthy',
                details={'error': str(e), 'error_type': type(e).__name__},
                timestamp=time.time(),
                latency_ms=latency_ms
            )
            
            self._generate_alert(AlertEvent(
                alert_type='observability_system_failure',
                severity='critical',
                component='observability_system',
                message=f"Observability system unreachable: {e}",
                timestamp=time.time(),
                metadata={'error': str(e), 'latency_ms': latency_ms}
            ))
            
            self.health_checks['observability_system'] = health_status
            logger.error(f"❌ Observability system unreachable: {e}")
            
            return health_status
    
    def collect_system_metrics(self) -> List[MetricData]:
        """Collect system-level metrics"""
        metrics = []
        timestamp = time.time()
        
        try:
            import psutil
            
            # CPU and memory metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics.extend([
                MetricData('system_cpu_percent', cpu_percent, timestamp, {}, 'percent'),
                MetricData('system_memory_percent', memory.percent, timestamp, {}, 'percent'),
                MetricData('system_memory_used_gb', memory.used / (1024**3), timestamp, {}, 'gigabytes'),
                MetricData('system_disk_percent', disk.percent, timestamp, {}, 'percent'),
                MetricData('system_disk_free_gb', disk.free / (1024**3), timestamp, {}, 'gigabytes'),
            ])
            
            # Track in performance tracker
            self.performance_tracker.record_metric('system_cpu_percent', cpu_percent)
            self.performance_tracker.record_metric('system_memory_percent', memory.percent)
            
            logger.debug(f"📊 System metrics - CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%")
            
        except ImportError:
            logger.warning("⚠️ psutil not available for system metrics")
        except Exception as e:
            logger.error(f"❌ Failed to collect system metrics: {e}")
        
        return metrics
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for dashboard"""
        
        # Run all health checks
        credential_health = self.check_credential_provider_health()
        observability_health = self.check_observability_system_health()
        
        # Collect current metrics
        system_metrics = self.collect_system_metrics()
        
        # Calculate performance statistics
        wrapper_stats = self.performance_tracker.get_stats('wrapper_execution_time_ms')
        success_rate_recent = self.performance_tracker.get_recent_average('wrapper_success_rate', 300)  # 5 min
        
        # Overall system status
        all_statuses = [credential_health.status, observability_health.status]
        if 'unhealthy' in all_statuses:
            overall_status = 'unhealthy'
        elif 'degraded' in all_statuses:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        status = {
            'overall_status': overall_status,
            'timestamp': time.time(),
            'uptime_seconds': time.time() - self.start_time,
            'health_checks': {
                'credential_provider': asdict(credential_health),
                'observability_system': asdict(observability_health),
            },
            'performance_metrics': {
                'wrapper_execution_stats': wrapper_stats,
                'success_rate_5min': success_rate_recent,
                'available_api_keys': self.performance_tracker.get_recent_average('available_api_keys_count', 60),
                'observability_connections': self.performance_tracker.get_recent_average('observability_active_connections', 60),
            },
            'system_metrics': {
                'cpu_percent': self.performance_tracker.get_recent_average('system_cpu_percent', 60),
                'memory_percent': self.performance_tracker.get_recent_average('system_memory_percent', 60),
            },
            'recent_alerts': [asdict(alert) for alert in list(self.alert_history)[-10:]],
            'configuration': self.config
        }
        
        return status
    
    def _generate_alert(self, alert: AlertEvent):
        """Generate and store alert"""
        self.alert_history.append(alert)
        
        # Log alert
        severity_emoji = {'critical': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}
        emoji = severity_emoji.get(alert.severity, '📢')
        logger.warning(f"{emoji} ALERT [{alert.severity.upper()}] {alert.component}: {alert.message}")
        
        # TODO: Send to external alerting system (PagerDuty, Slack, etc.)
        # self._send_external_alert(alert)
    
    def export_metrics_to_observability(self, metrics: List[MetricData]) -> bool:
        """Export metrics to observability system"""
        try:
            # Format metrics for observability system
            events = []
            for metric in metrics:
                event_data = {
                    'source_app': 'hook-wrapper-monitoring',
                    'session_id': 'monitoring_system',
                    'hook_event_type': 'MetricReport',
                    'payload': asdict(metric),
                    'timestamp': int(metric.timestamp * 1000)
                }
                events.append(event_data)
            
            # Send to observability server
            for event in events:
                response = requests.post(
                    'http://localhost:4000/events',
                    json=event,
                    timeout=5
                )
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Failed to export metric: HTTP {response.status_code}")
                    return False
            
            logger.debug(f"📊 Exported {len(metrics)} metrics to observability system")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export metrics: {e}")
            return False

# Global monitoring instance
_monitoring_instance = None
_monitoring_lock = threading.Lock()

def get_monitoring_instance() -> MonitoringCollector:
    """Get singleton monitoring instance"""
    global _monitoring_instance
    with _monitoring_lock:
        if _monitoring_instance is None:
            _monitoring_instance = MonitoringCollector()
        return _monitoring_instance

def record_wrapper_execution(execution_time: float, hook_name: str, 
                           success: bool, credentials_loaded: int):
    """Convenience function to record wrapper execution metrics"""
    monitoring = get_monitoring_instance()
    metric = monitoring.collect_wrapper_metrics(execution_time, hook_name, success, credentials_loaded)
    monitoring.export_metrics_to_observability([metric])

def get_system_health() -> Dict[str, Any]:
    """Convenience function to get system health status"""
    monitoring = get_monitoring_instance()
    return monitoring.get_comprehensive_status()

if __name__ == '__main__':
    # CLI interface for monitoring system
    import argparse
    
    parser = argparse.ArgumentParser(description='Hook Wrapper Monitoring System')
    parser.add_argument('--status', action='store_true', help='Show comprehensive system status')
    parser.add_argument('--health-check', action='store_true', help='Run health checks')
    parser.add_argument('--metrics', action='store_true', help='Show performance metrics')
    parser.add_argument('--alerts', action='store_true', help='Show recent alerts')
    parser.add_argument('--export', action='store_true', help='Export current metrics')
    
    args = parser.parse_args()
    
    monitoring = get_monitoring_instance()
    
    if args.status:
        status = monitoring.get_comprehensive_status()
        print(json.dumps(status, indent=2, default=str))
    elif args.health_check:
        print("🔍 Running health checks...")
        cred_health = monitoring.check_credential_provider_health()
        obs_health = monitoring.check_observability_system_health()
        print(f"Credential Provider: {cred_health.status}")
        print(f"Observability System: {obs_health.status}")
    elif args.metrics:
        print("📊 Performance Metrics:")
        stats = monitoring.performance_tracker.get_stats('wrapper_execution_time_ms')
        if stats:
            for key, value in stats.items():
                print(f"  {key}: {value}")
    elif args.alerts:
        print("🚨 Recent Alerts:")
        for alert in list(monitoring.alert_history)[-10:]:
            print(f"  [{alert.severity}] {alert.component}: {alert.message}")
    elif args.export:
        metrics = monitoring.collect_system_metrics()
        success = monitoring.export_metrics_to_observability(metrics)
        print(f"Export {'successful' if success else 'failed'}")
    else:
        # Default: show brief status
        status = monitoring.get_comprehensive_status()
        print(f"Overall Status: {status['overall_status']}")
        print(f"Uptime: {status['uptime_seconds']:.0f} seconds")
        print(f"Success Rate (5min): {status['performance_metrics']['success_rate_5min']:.1%}")