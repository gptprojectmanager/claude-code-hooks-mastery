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
Health Check Server for Hook Wrapper Infrastructure
==================================================

This module provides HTTP endpoints for monitoring the health and performance
of the hook wrapper system, credential provider, and observability integration.

Key Features:
- RESTful API for health checks and metrics
- Real-time status monitoring
- Performance metrics exposition
- Integration with monitoring systems
- Automated diagnostic endpoints
- Alert status reporting

Endpoints:
- GET /health - Overall system health
- GET /health/credential-provider - Credential provider health
- GET /health/observability - Observability system health
- GET /metrics - Performance metrics
- GET /metrics/wrapper - Hook wrapper metrics
- GET /metrics/system - System resource metrics
- GET /alerts - Recent alerts
- GET /status - Comprehensive status report

Usage:
    python health_check_server.py [--port 8080] [--host 0.0.0.0]
    
The server integrates with the monitoring system to provide real-time
health status and performance data for operational monitoring.
"""

import os
import sys
import json
import time
import argparse
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Setup logging
log_dir = Path.home() / ".claude" / "logs" / "health_check"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"health_check_{time.strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('health_check_server')

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health check endpoints"""
    
    def __init__(self, *args, monitoring_system=None, **kwargs):
        self.monitoring_system = monitoring_system
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            url_parts = urlparse(self.path)
            path = url_parts.path
            query_params = parse_qs(url_parts.query)
            
            # Route requests to appropriate handlers
            if path == '/health':
                self._handle_overall_health()
            elif path == '/health/credential-provider':
                self._handle_credential_health()
            elif path == '/health/observability':
                self._handle_observability_health()
            elif path == '/metrics':
                self._handle_metrics()
            elif path == '/metrics/wrapper':
                self._handle_wrapper_metrics()
            elif path == '/metrics/system':
                self._handle_system_metrics()
            elif path == '/alerts':
                self._handle_alerts()
            elif path == '/status':
                self._handle_comprehensive_status()
            elif path == '/ping':
                self._handle_ping()
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling request {self.path}: {e}")
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def _handle_overall_health(self):
        """Handle overall system health check"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            # Get comprehensive status
            status = self.monitoring_system.get_comprehensive_status()
            
            # Create health response
            health_response = {
                'status': status['overall_status'],
                'timestamp': status['timestamp'],
                'uptime_seconds': status['uptime_seconds'],
                'checks': {
                    'credential_provider': status['health_checks']['credential_provider']['status'],
                    'observability_system': status['health_checks']['observability_system']['status'],
                },
                'metrics': {
                    'wrapper_success_rate': status['performance_metrics']['success_rate_5min'],
                    'available_api_keys': status['performance_metrics']['available_api_keys'],
                    'cpu_percent': status['system_metrics']['cpu_percent'],
                    'memory_percent': status['system_metrics']['memory_percent'],
                }
            }
            
            # Determine HTTP status code
            if status['overall_status'] == 'healthy':
                http_status = 200
            elif status['overall_status'] == 'degraded':
                http_status = 200  # Still responding but with warnings
            else:
                http_status = 503  # Service unavailable
            
            self._send_json_response(health_response, http_status)
            
        except Exception as e:
            logger.error(f"Error in overall health check: {e}")
            self._send_error(500, "Health check failed")
    
    def _handle_credential_health(self):
        """Handle credential provider specific health check"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            health_status = self.monitoring_system.check_credential_provider_health()
            
            response = {
                'component': health_status.component,
                'status': health_status.status,
                'latency_ms': health_status.latency_ms,
                'timestamp': health_status.timestamp,
                'details': health_status.details
            }
            
            # HTTP status based on health
            http_status = 200 if health_status.status in ['healthy', 'degraded'] else 503
            
            self._send_json_response(response, http_status)
            
        except Exception as e:
            logger.error(f"Error in credential provider health check: {e}")
            self._send_error(500, "Credential provider health check failed")
    
    def _handle_observability_health(self):
        """Handle observability system specific health check"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            health_status = self.monitoring_system.check_observability_system_health()
            
            response = {
                'component': health_status.component,
                'status': health_status.status,
                'latency_ms': health_status.latency_ms,
                'timestamp': health_status.timestamp,
                'details': health_status.details
            }
            
            # HTTP status based on health
            http_status = 200 if health_status.status in ['healthy', 'degraded'] else 503
            
            self._send_json_response(response, http_status)
            
        except Exception as e:
            logger.error(f"Error in observability health check: {e}")
            self._send_error(500, "Observability health check failed")
    
    def _handle_metrics(self):
        """Handle metrics endpoint - returns all metrics"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            # Collect all metrics
            wrapper_stats = self.monitoring_system.performance_tracker.get_stats('wrapper_execution_time_ms')
            success_rate = self.monitoring_system.performance_tracker.get_recent_average('wrapper_success_rate', 300)
            api_keys = self.monitoring_system.performance_tracker.get_recent_average('available_api_keys_count', 60)
            
            # System metrics
            cpu_percent = self.monitoring_system.performance_tracker.get_recent_average('system_cpu_percent', 60)
            memory_percent = self.monitoring_system.performance_tracker.get_recent_average('system_memory_percent', 60)
            
            metrics = {
                'timestamp': time.time(),
                'wrapper_performance': wrapper_stats,
                'success_rate_5min': success_rate,
                'available_api_keys': api_keys,
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                },
                'observability': {
                    'active_connections': self.monitoring_system.performance_tracker.get_recent_average('observability_active_connections', 60),
                    'uptime': self.monitoring_system.performance_tracker.get_recent_average('observability_uptime_seconds', 60),
                }
            }
            
            self._send_json_response(metrics)
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            self._send_error(500, "Failed to retrieve metrics")
    
    def _handle_wrapper_metrics(self):
        """Handle wrapper-specific metrics"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            # Get wrapper performance statistics
            execution_stats = self.monitoring_system.performance_tracker.get_stats('wrapper_execution_time_ms')
            success_stats = self.monitoring_system.performance_tracker.get_stats('wrapper_success_rate')
            credentials_stats = self.monitoring_system.performance_tracker.get_stats('credentials_loaded_count')
            
            wrapper_metrics = {
                'timestamp': time.time(),
                'execution_time_ms': execution_stats,
                'success_rate': success_stats,
                'credentials_loaded': credentials_stats,
                'recent_averages': {
                    'execution_time_1min': self.monitoring_system.performance_tracker.get_recent_average('wrapper_execution_time_ms', 60),
                    'execution_time_5min': self.monitoring_system.performance_tracker.get_recent_average('wrapper_execution_time_ms', 300),
                    'success_rate_1min': self.monitoring_system.performance_tracker.get_recent_average('wrapper_success_rate', 60),
                    'success_rate_5min': self.monitoring_system.performance_tracker.get_recent_average('wrapper_success_rate', 300),
                }
            }
            
            self._send_json_response(wrapper_metrics)
            
        except Exception as e:
            logger.error(f"Error retrieving wrapper metrics: {e}")
            self._send_error(500, "Failed to retrieve wrapper metrics")
    
    def _handle_system_metrics(self):
        """Handle system resource metrics"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            # Collect fresh system metrics
            system_metrics_list = self.monitoring_system.collect_system_metrics()
            
            # Format for response
            system_data = {
                'timestamp': time.time(),
                'current_metrics': {},
                'averages': {
                    'cpu_1min': self.monitoring_system.performance_tracker.get_recent_average('system_cpu_percent', 60),
                    'cpu_5min': self.monitoring_system.performance_tracker.get_recent_average('system_cpu_percent', 300),
                    'memory_1min': self.monitoring_system.performance_tracker.get_recent_average('system_memory_percent', 60),
                    'memory_5min': self.monitoring_system.performance_tracker.get_recent_average('system_memory_percent', 300),
                }
            }
            
            # Add current metrics
            for metric in system_metrics_list:
                system_data['current_metrics'][metric.metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'tags': metric.tags
                }
            
            self._send_json_response(system_data)
            
        except Exception as e:
            logger.error(f"Error retrieving system metrics: {e}")
            self._send_error(500, "Failed to retrieve system metrics")
    
    def _handle_alerts(self):
        """Handle alerts endpoint"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            # Get recent alerts
            alerts = []
            for alert in list(self.monitoring_system.alert_history):
                alerts.append({
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'component': alert.component,
                    'message': alert.message,
                    'timestamp': alert.timestamp,
                    'metadata': alert.metadata
                })
            
            # Sort by timestamp (most recent first)
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            alert_response = {
                'total_alerts': len(alerts),
                'alerts': alerts[:50],  # Limit to 50 most recent
                'summary': {
                    'critical': len([a for a in alerts if a['severity'] == 'critical']),
                    'warning': len([a for a in alerts if a['severity'] == 'warning']),
                    'info': len([a for a in alerts if a['severity'] == 'info']),
                }
            }
            
            self._send_json_response(alert_response)
            
        except Exception as e:
            logger.error(f"Error retrieving alerts: {e}")
            self._send_error(500, "Failed to retrieve alerts")
    
    def _handle_comprehensive_status(self):
        """Handle comprehensive status endpoint"""
        try:
            if not self.monitoring_system:
                self._send_error(503, "Monitoring system not available")
                return
            
            status = self.monitoring_system.get_comprehensive_status()
            self._send_json_response(status)
            
        except Exception as e:
            logger.error(f"Error retrieving comprehensive status: {e}")
            self._send_error(500, "Failed to retrieve comprehensive status")
    
    def _handle_ping(self):
        """Handle simple ping endpoint"""
        ping_response = {
            'status': 'ok',
            'timestamp': time.time(),
            'service': 'hook-wrapper-health-check'
        }
        self._send_json_response(ping_response)
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response"""
        try:
            json_data = json.dumps(data, indent=2, default=str)
            
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(json_data)))
            self.end_headers()
            
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error sending JSON response: {e}")
            self._send_error(500, "Failed to serialize response")
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        error_data = {
            'error': message,
            'status_code': status_code,
            'timestamp': time.time()
        }
        
        try:
            json_data = json.dumps(error_data, indent=2)
            
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(json_data)))
            self.end_headers()
            
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error sending error response: {e}")
            # Fallback to simple text response
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Internal server error')
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.info(f"{self.address_string()} - {format % args}")

class HealthCheckServer:
    """Health check server for hook wrapper infrastructure"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.server = None
        self.monitoring_system = None
        self.running = False
        
        # Initialize monitoring system
        try:
            from monitoring_system import get_monitoring_instance
            self.monitoring_system = get_monitoring_instance()
            logger.info("✅ Monitoring system connected")
        except ImportError:
            logger.warning("⚠️ Monitoring system not available")
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring system: {e}")
    
    def start(self):
        """Start the health check server"""
        try:
            # Create handler with monitoring system
            def handler_factory(*args, **kwargs):
                return HealthCheckHandler(*args, monitoring_system=self.monitoring_system, **kwargs)
            
            # Create HTTP server
            self.server = HTTPServer((self.host, self.port), handler_factory)
            self.running = True
            
            logger.info(f"🌐 Health check server starting on http://{self.host}:{self.port}")
            logger.info("📊 Available endpoints:")
            logger.info("  GET /health - Overall system health")
            logger.info("  GET /health/credential-provider - Credential provider health")
            logger.info("  GET /health/observability - Observability system health")
            logger.info("  GET /metrics - Performance metrics")
            logger.info("  GET /metrics/wrapper - Hook wrapper metrics")
            logger.info("  GET /metrics/system - System resource metrics")
            logger.info("  GET /alerts - Recent alerts")
            logger.info("  GET /status - Comprehensive status")
            logger.info("  GET /ping - Simple health check")
            
            # Start server
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down health check server...")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Failed to start health check server: {e}")
            raise
    
    def stop(self):
        """Stop the health check server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            logger.info("✅ Health check server stopped")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Hook Wrapper Health Check Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon process')
    
    args = parser.parse_args()
    
    try:
        server = HealthCheckServer(host=args.host, port=args.port)
        
        if args.daemon:
            # TODO: Implement proper daemon mode
            logger.info("🔧 Daemon mode not yet implemented, running in foreground")
        
        server.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()