#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
# ]
# ///

"""
Monitoring Dashboard Integration for Hook Wrapper Infrastructure
===============================================================

This module provides dashboard integration capabilities for the hook wrapper
monitoring system, extending the existing observability system with dedicated
hook wrapper monitoring views and real-time status updates.

Key Features:
- Dashboard data formatting for existing observability UI
- Real-time monitoring data streams
- Performance visualization data preparation
- Alert aggregation for dashboard display
- Integration with existing WebSocket infrastructure
- Metrics transformation for charts and graphs

Integration Points:
- Observability server WebSocket for real-time updates
- Dashboard API endpoints for historical data
- Alert management integration
- Performance metrics visualization

Usage:
    from monitoring_dashboard import DashboardIntegration
    
    dashboard = DashboardIntegration()
    dashboard.start_monitoring_stream()
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import asdict
import requests

# Setup logging
logger = logging.getLogger('monitoring_dashboard')

class DashboardIntegration:
    """
    Dashboard integration for hook wrapper monitoring data.
    
    This class provides the bridge between the monitoring system
    and the existing observability dashboard, formatting data
    appropriately and streaming updates in real-time.
    """
    
    def __init__(self, observability_url: str = 'http://localhost:4000'):
        self.observability_url = observability_url
        self.monitoring_system = None
        self.streaming_thread = None
        self.streaming_active = False
        self.update_interval = 10  # seconds
        
        # Initialize monitoring system connection
        try:
            from monitoring_system import get_monitoring_instance
            self.monitoring_system = get_monitoring_instance()
            logger.info("✅ Connected to monitoring system")
        except ImportError:
            logger.warning("⚠️ Monitoring system not available")
        except Exception as e:
            logger.error(f"❌ Failed to connect to monitoring system: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get formatted data for dashboard display.
        
        Returns:
            Formatted data structure for dashboard consumption
        """
        if not self.monitoring_system:
            return self._get_fallback_data()
        
        try:
            # Get comprehensive status from monitoring system
            status = self.monitoring_system.get_comprehensive_status()
            
            # Format for dashboard
            dashboard_data = {
                'timestamp': status['timestamp'],
                'overall_status': status['overall_status'],
                'uptime_seconds': status['uptime_seconds'],
                'components': self._format_component_status(status),
                'performance': self._format_performance_metrics(status),
                'alerts': self._format_alerts(status),
                'charts': self._prepare_chart_data(status),
                'system_info': self._format_system_info(status)
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self._get_fallback_data()
    
    def _format_component_status(self, status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format component health status for dashboard"""
        components = []
        
        # Credential Provider
        cred_health = status['health_checks'].get('credential_provider', {})
        components.append({
            'name': 'Credential Provider',
            'status': cred_health.get('status', 'unknown'),
            'latency_ms': cred_health.get('latency_ms', 0),
            'details': {
                'available_keys': status['performance_metrics'].get('available_api_keys', 0),
                'cache_valid': cred_health.get('details', {}).get('cache_status', {}).get('cache_valid', False),
                'secret_manager': cred_health.get('details', {}).get('secret_manager_available', False)
            }
        })
        
        # Observability System
        obs_health = status['health_checks'].get('observability_system', {})
        components.append({
            'name': 'Observability System',
            'status': obs_health.get('status', 'unknown'),
            'latency_ms': obs_health.get('latency_ms', 0),
            'details': {
                'active_connections': status['performance_metrics'].get('observability_connections', 0),
                'server_uptime': obs_health.get('details', {}).get('metrics', {}).get('uptime', 0)
            }
        })
        
        # Hook Wrapper Performance
        wrapper_success = status['performance_metrics'].get('success_rate_5min', 1.0)
        wrapper_status = 'healthy' if wrapper_success > 0.95 else 'degraded' if wrapper_success > 0.8 else 'unhealthy'
        
        components.append({
            'name': 'Hook Wrapper',
            'status': wrapper_status,
            'latency_ms': status['performance_metrics'].get('wrapper_execution_stats', {}).get('mean', 0),
            'details': {
                'success_rate': wrapper_success,
                'avg_execution_ms': status['performance_metrics'].get('wrapper_execution_stats', {}).get('mean', 0),
                'p95_execution_ms': status['performance_metrics'].get('wrapper_execution_stats', {}).get('p95', 0)
            }
        })
        
        return components
    
    def _format_performance_metrics(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Format performance metrics for dashboard"""
        wrapper_stats = status['performance_metrics'].get('wrapper_execution_stats', {})
        
        return {
            'wrapper': {
                'execution_time': {
                    'mean': wrapper_stats.get('mean', 0),
                    'median': wrapper_stats.get('median', 0),
                    'p95': wrapper_stats.get('p95', 0),
                    'p99': wrapper_stats.get('p99', 0),
                    'max': wrapper_stats.get('max', 0)
                },
                'success_rate': status['performance_metrics'].get('success_rate_5min', 1.0),
                'throughput': wrapper_stats.get('count', 0)
            },
            'system': {
                'cpu_percent': status['system_metrics'].get('cpu_percent', 0),
                'memory_percent': status['system_metrics'].get('memory_percent', 0)
            },
            'credentials': {
                'available_keys': status['performance_metrics'].get('available_api_keys', 0)
            }
        }
    
    def _format_alerts(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Format alerts for dashboard display"""
        recent_alerts = status.get('recent_alerts', [])
        
        # Categorize alerts
        alert_summary = {
            'total': len(recent_alerts),
            'critical': len([a for a in recent_alerts if a.get('severity') == 'critical']),
            'warning': len([a for a in recent_alerts if a.get('severity') == 'warning']),
            'info': len([a for a in recent_alerts if a.get('severity') == 'info'])
        }
        
        # Format recent alerts for display
        formatted_alerts = []
        for alert in recent_alerts[-10:]:  # Last 10 alerts
            formatted_alerts.append({
                'severity': alert.get('severity', 'info'),
                'component': alert.get('component', 'unknown'),
                'message': alert.get('message', ''),
                'timestamp': alert.get('timestamp', time.time()),
                'time_ago': self._format_time_ago(alert.get('timestamp', time.time()))
            })
        
        return {
            'summary': alert_summary,
            'recent': formatted_alerts
        }
    
    def _prepare_chart_data(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for dashboard charts"""
        if not self.monitoring_system:
            return {}
        
        # Get historical data for charts
        current_time = time.time()
        
        # Performance chart data (last hour, 5-minute intervals)
        performance_data = []
        for i in range(12):  # 12 intervals of 5 minutes = 1 hour
            timestamp = current_time - (i * 300)  # 5 minutes ago
            success_rate = self.monitoring_system.performance_tracker.get_recent_average('wrapper_success_rate', 300)
            exec_time = self.monitoring_system.performance_tracker.get_recent_average('wrapper_execution_time_ms', 300)
            
            performance_data.append({
                'timestamp': timestamp,
                'success_rate': success_rate,
                'execution_time_ms': exec_time
            })
        
        performance_data.reverse()  # Oldest first
        
        # System resource chart data
        system_data = []
        for i in range(12):
            timestamp = current_time - (i * 300)
            cpu = self.monitoring_system.performance_tracker.get_recent_average('system_cpu_percent', 300)
            memory = self.monitoring_system.performance_tracker.get_recent_average('system_memory_percent', 300)
            
            system_data.append({
                'timestamp': timestamp,
                'cpu_percent': cpu,
                'memory_percent': memory
            })
        
        system_data.reverse()
        
        return {
            'performance_timeline': performance_data,
            'system_resources': system_data,
            'alert_timeline': self._get_alert_timeline()
        }
    
    def _get_alert_timeline(self) -> List[Dict[str, Any]]:
        """Get alert timeline for dashboard chart"""
        if not self.monitoring_system:
            return []
        
        # Group alerts by hour for the last 24 hours
        current_time = time.time()
        timeline = []
        
        for i in range(24):  # Last 24 hours
            hour_start = current_time - (i * 3600)  # 1 hour ago
            hour_end = hour_start + 3600
            
            # Count alerts in this hour
            hour_alerts = [
                alert for alert in self.monitoring_system.alert_history
                if hour_start <= alert.timestamp < hour_end
            ]
            
            timeline.append({
                'timestamp': hour_start,
                'alert_count': len(hour_alerts),
                'critical_count': len([a for a in hour_alerts if a.severity == 'critical']),
                'warning_count': len([a for a in hour_alerts if a.severity == 'warning'])
            })
        
        timeline.reverse()  # Oldest first
        return timeline
    
    def _format_system_info(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Format system information for dashboard"""
        return {
            'uptime': status.get('uptime_seconds', 0),
            'uptime_formatted': self._format_uptime(status.get('uptime_seconds', 0)),
            'configuration': status.get('configuration', {}),
            'version': '1.0.0',  # TODO: Get from version file
            'environment': 'production'  # TODO: Detect environment
        }
    
    def _format_time_ago(self, timestamp: float) -> str:
        """Format timestamp as time ago string"""
        now = time.time()
        diff = now - timestamp
        
        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff / 60)}m ago"
        elif diff < 86400:
            return f"{int(diff / 3600)}h ago"
        else:
            return f"{int(diff / 86400)}d ago"
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format"""
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Get fallback data when monitoring system is unavailable"""
        return {
            'timestamp': time.time(),
            'overall_status': 'unknown',
            'uptime_seconds': 0,
            'components': [
                {
                    'name': 'Monitoring System',
                    'status': 'unhealthy',
                    'latency_ms': 0,
                    'details': {'error': 'Monitoring system not available'}
                }
            ],
            'performance': {
                'wrapper': {'execution_time': {}, 'success_rate': 0, 'throughput': 0},
                'system': {'cpu_percent': 0, 'memory_percent': 0},
                'credentials': {'available_keys': 0}
            },
            'alerts': {'summary': {'total': 0, 'critical': 0, 'warning': 0, 'info': 0}, 'recent': []},
            'charts': {'performance_timeline': [], 'system_resources': [], 'alert_timeline': []},
            'system_info': {
                'uptime': 0,
                'uptime_formatted': '0m',
                'configuration': {},
                'version': '1.0.0',
                'environment': 'unknown'
            }
        }
    
    def send_monitoring_update(self) -> bool:
        """Send monitoring data update to observability system"""
        try:
            # Get dashboard data
            dashboard_data = self.get_dashboard_data()
            
            # Format as observability event
            event_data = {
                'source_app': 'hook-wrapper-monitoring-dashboard',
                'session_id': 'monitoring_dashboard',
                'hook_event_type': 'MonitoringUpdate',
                'payload': dashboard_data,
                'timestamp': int(time.time() * 1000)
            }
            
            # Send to observability server
            response = requests.post(
                f'{self.observability_url}/events',
                json=event_data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug("📊 Sent monitoring update to observability system")
                return True
            else:
                logger.warning(f"⚠️ Failed to send monitoring update: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Failed to send monitoring update: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending monitoring update: {e}")
            return False
    
    def start_monitoring_stream(self):
        """Start streaming monitoring updates to observability system"""
        if self.streaming_active:
            logger.warning("⚠️ Monitoring stream already active")
            return
        
        def stream_worker():
            logger.info("🔄 Starting monitoring data stream")
            self.streaming_active = True
            
            while self.streaming_active:
                try:
                    # Send monitoring update
                    self.send_monitoring_update()
                    
                    # Wait for next update
                    time.sleep(self.update_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Error in monitoring stream: {e}")
                    time.sleep(self.update_interval)
            
            logger.info("🛑 Monitoring data stream stopped")
        
        self.streaming_thread = threading.Thread(target=stream_worker, daemon=True)
        self.streaming_thread.start()
        
        logger.info(f"🚀 Monitoring stream started (interval: {self.update_interval}s)")
    
    def stop_monitoring_stream(self):
        """Stop streaming monitoring updates"""
        if not self.streaming_active:
            return
        
        self.streaming_active = False
        if self.streaming_thread:
            self.streaming_thread.join(timeout=5)
        
        logger.info("✅ Monitoring stream stopped")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get concise performance summary for quick status checks"""
        dashboard_data = self.get_dashboard_data()
        
        return {
            'overall_status': dashboard_data['overall_status'],
            'wrapper_success_rate': dashboard_data['performance']['wrapper']['success_rate'],
            'avg_execution_ms': dashboard_data['performance']['wrapper']['execution_time'].get('mean', 0),
            'available_api_keys': dashboard_data['performance']['credentials']['available_keys'],
            'recent_alerts': dashboard_data['alerts']['summary']['total'],
            'uptime': dashboard_data['system_info']['uptime_formatted']
        }

# Global dashboard instance
_dashboard_instance = None

def get_dashboard_instance() -> DashboardIntegration:
    """Get singleton dashboard instance"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = DashboardIntegration()
    return _dashboard_instance

if __name__ == '__main__':
    # CLI interface for dashboard integration
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring Dashboard Integration')
    parser.add_argument('--start-stream', action='store_true', help='Start monitoring data stream')
    parser.add_argument('--get-data', action='store_true', help='Get current dashboard data')
    parser.add_argument('--summary', action='store_true', help='Get performance summary')
    parser.add_argument('--send-update', action='store_true', help='Send single monitoring update')
    
    args = parser.parse_args()
    
    dashboard = get_dashboard_instance()
    
    if args.start_stream:
        dashboard.start_monitoring_stream()
        try:
            # Keep running until interrupted
            import signal
            signal.pause()
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring stream...")
            dashboard.stop_monitoring_stream()
    elif args.get_data:
        data = dashboard.get_dashboard_data()
        print(json.dumps(data, indent=2, default=str))
    elif args.summary:
        summary = dashboard.get_performance_summary()
        print(json.dumps(summary, indent=2, default=str))
    elif args.send_update:
        success = dashboard.send_monitoring_update()
        print(f"Update {'sent successfully' if success else 'failed'}")
    else:
        # Default: show brief status
        summary = dashboard.get_performance_summary()
        print("📊 Hook Wrapper Monitoring Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")