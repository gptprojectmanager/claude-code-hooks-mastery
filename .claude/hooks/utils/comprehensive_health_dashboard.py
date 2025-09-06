#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "flask",
#     "flask-cors",
#     "psutil",
# ]
# ///

"""
Comprehensive Health Dashboard for Hook Wrapper Infrastructure
==============================================================

This module provides a web-based dashboard for monitoring the health and
performance of the hook wrapper system, integrating with the enhanced
monitoring system and existing observability infrastructure.

Key Features:
- Real-time health status visualization
- Performance metrics and trends
- Alert management interface
- Diagnostic results display
- System resource monitoring
- API endpoint for external integration

Dashboard Components:
- System overview with status indicators
- Performance charts and metrics
- Alert timeline and management
- Diagnostic results and recommendations
- Configuration and baseline management

Usage:
    python comprehensive_health_dashboard.py [--port 8081] [--debug]
    
The dashboard runs as a Flask web application providing:
- Web UI at http://localhost:8081/
- API endpoints for programmatic access
- Integration with existing observability system
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from flask import Flask, render_template_string, jsonify, request, send_from_directory
from flask_cors import CORS
import requests

# Setup logging
log_dir = Path.home() / ".claude" / "logs" / "health_dashboard"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"health_dashboard_{time.strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('health_dashboard')

class HealthDashboard:
    """Comprehensive health dashboard for hook wrapper monitoring"""
    
    def __init__(self, port: int = 8081, debug: bool = False):
        self.port = port
        self.debug = debug
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Dashboard state
        self.last_update = 0
        self.cached_status = {}
        self.cache_ttl = 10  # seconds
        
        # Setup routes
        self.setup_routes()
        
        logger.info("🖥️ Health Dashboard initialized")
    
    def setup_routes(self):
        """Setup Flask routes for the dashboard"""
        
        @self.app.route('/')
        def dashboard_home():
            """Main dashboard page"""
            return render_template_string(DASHBOARD_HTML_TEMPLATE)
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for comprehensive status"""
            try:
                status = self.get_comprehensive_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"❌ Error in /api/status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def api_health():
            """API endpoint for basic health check"""
            try:
                status = self.get_basic_health()
                return jsonify(status)
            except Exception as e:
                logger.error(f"❌ Error in /api/health: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """API endpoint for performance metrics"""
            try:
                metrics = self.get_performance_metrics()
                return jsonify(metrics)
            except Exception as e:
                logger.error(f"❌ Error in /api/metrics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """API endpoint for alerts"""
            try:
                alerts = self.get_alerts()
                return jsonify(alerts)
            except Exception as e:
                logger.error(f"❌ Error in /api/alerts: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/diagnostics')
        def api_diagnostics():
            """API endpoint for diagnostic results"""
            try:
                diagnostics = self.get_diagnostics()
                return jsonify(diagnostics)
            except Exception as e:
                logger.error(f"❌ Error in /api/diagnostics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/diagnostics/run', methods=['POST'])
        def api_run_diagnostics():
            """API endpoint to trigger diagnostic run"""
            try:
                results = self.run_diagnostics()
                return jsonify({'success': True, 'results': results})
            except Exception as e:
                logger.error(f"❌ Error running diagnostics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/baselines')
        def api_baselines():
            """API endpoint for performance baselines"""
            try:
                baselines = self.get_baselines()
                return jsonify(baselines)
            except Exception as e:
                logger.error(f"❌ Error in /api/baselines: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/system-info')
        def api_system_info():
            """API endpoint for system information"""
            try:
                system_info = self.get_system_info()
                return jsonify(system_info)
            except Exception as e:
                logger.error(f"❌ Error in /api/system-info: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/test-alert', methods=['POST'])
        def api_test_alert():
            """API endpoint to test alert system"""
            try:
                result = self.test_alert_system()
                return jsonify({'success': True, 'result': result})
            except Exception as e:
                logger.error(f"❌ Error testing alerts: {e}")
                return jsonify({'error': str(e)}), 500
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status with caching"""
        current_time = time.time()
        
        # Check cache
        if (current_time - self.last_update) < self.cache_ttl and self.cached_status:
            return self.cached_status
        
        try:
            # Try to get status from enhanced monitoring system
            from enhanced_monitoring_system import get_enhanced_monitoring_instance
            enhanced_monitoring = get_enhanced_monitoring_instance()
            status = enhanced_monitoring.get_comprehensive_status()
            
            # Update cache
            self.cached_status = status
            self.last_update = current_time
            
            return status
            
        except ImportError:
            logger.warning("⚠️ Enhanced monitoring system not available, using fallback")
            return self.get_fallback_status()
        except Exception as e:
            logger.error(f"❌ Error getting comprehensive status: {e}")
            return self.get_fallback_status()
    
    def get_fallback_status(self) -> Dict[str, Any]:
        """Get fallback status when enhanced monitoring is unavailable"""
        try:
            # Try basic monitoring system
            from monitoring_system import get_monitoring_instance
            monitoring = get_monitoring_instance()
            return monitoring.get_comprehensive_status()
            
        except ImportError:
            logger.warning("⚠️ Basic monitoring system not available")
            return {
                'overall_status': 'unknown',
                'timestamp': time.time(),
                'error': 'Monitoring systems unavailable',
                'components': [],
                'performance_metrics': {},
                'alerts': {'summary': {'total': 0}, 'recent': []},
                'enhanced_monitoring': {'system_active': False}
            }
        except Exception as e:
            logger.error(f"❌ Error in fallback status: {e}")
            return {
                'overall_status': 'error',
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def get_basic_health(self) -> Dict[str, Any]:
        """Get basic health status for quick checks"""
        status = self.get_comprehensive_status()
        
        return {
            'status': status.get('overall_status', 'unknown'),
            'timestamp': status.get('timestamp', time.time()),
            'uptime_seconds': status.get('uptime_seconds', 0),
            'components_healthy': len([
                c for c in status.get('health_checks', {}).values() 
                if c.get('status') == 'healthy'
            ]),
            'active_alerts': status.get('enhanced_monitoring', {}).get('alert_manager', {}).get('active_alerts_count', 0)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for dashboard charts"""
        status = self.get_comprehensive_status()
        
        performance = status.get('performance_metrics', {})
        wrapper_stats = performance.get('wrapper_execution_stats', {})
        
        return {
            'timestamp': status.get('timestamp', time.time()),
            'wrapper_performance': {
                'avg_execution_ms': wrapper_stats.get('mean', 0),
                'p95_execution_ms': wrapper_stats.get('p95', 0),
                'success_rate': performance.get('success_rate_5min', 1.0),
                'throughput': wrapper_stats.get('count', 0)
            },
            'system_resources': {
                'cpu_percent': status.get('system_metrics', {}).get('cpu_percent', 0),
                'memory_percent': status.get('system_metrics', {}).get('memory_percent', 0)
            },
            'credentials': {
                'available_keys': performance.get('available_api_keys', 0)
            },
            'observability': {
                'active_connections': performance.get('observability_connections', 0)
            }
        }
    
    def get_alerts(self) -> Dict[str, Any]:
        """Get alert information"""
        status = self.get_comprehensive_status()
        
        enhanced = status.get('enhanced_monitoring', {})
        alert_manager = enhanced.get('alert_manager', {})
        
        return {
            'summary': {
                'active_alerts': alert_manager.get('active_alerts_count', 0),
                'total_rules': alert_manager.get('total_rules', 0),
                'enabled_rules': alert_manager.get('enabled_rules', 0)
            },
            'active_alerts': alert_manager.get('active_alerts', []),
            'recent_alerts': alert_manager.get('recent_alerts', [])
        }
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic results"""
        status = self.get_comprehensive_status()
        
        enhanced = status.get('enhanced_monitoring', {})
        diagnostics = enhanced.get('diagnostics', {})
        
        return {
            'overall_status': diagnostics.get('overall_status', 'unknown'),
            'summary': diagnostics.get('summary', {}),
            'results': diagnostics.get('results', []),
            'last_run': enhanced.get('last_activities', {}).get('diagnostic_run', 0)
        }
    
    def get_baselines(self) -> Dict[str, Any]:
        """Get performance baselines"""
        status = self.get_comprehensive_status()
        
        enhanced = status.get('enhanced_monitoring', {})
        baseline_manager = enhanced.get('baseline_manager', {})
        
        return {
            'total_baselines': baseline_manager.get('total_baselines', 0),
            'baselines': baseline_manager.get('baselines', {}),
            'last_update': baseline_manager.get('last_update', 0)
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network info
            network = psutil.net_io_counters()
            
            # Get process info
            process = psutil.Process()
            
            return {
                'system': {
                    'cpu_percent': cpu_percent,
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_percent': memory.percent,
                    'disk_total_gb': disk.total / (1024**3),
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_percent': disk.percent,
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv
                },
                'process': {
                    'pid': process.pid,
                    'memory_percent': process.memory_percent(),
                    'cpu_percent': process.cpu_percent(),
                    'create_time': process.create_time(),
                    'num_threads': process.num_threads()
                },
                'python': {
                    'version': sys.version,
                    'executable': sys.executable,
                    'platform': sys.platform
                },
                'timestamp': time.time()
            }
            
        except ImportError:
            return {
                'error': 'psutil not available',
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': time.time()
            }
    
    def run_diagnostics(self) -> List[Dict[str, Any]]:
        """Run diagnostic checks"""
        try:
            from enhanced_monitoring_system import get_enhanced_monitoring_instance
            enhanced_monitoring = get_enhanced_monitoring_instance()
            results = enhanced_monitoring.run_immediate_diagnostic()
            
            return [
                {
                    'diagnostic_id': r.diagnostic_id,
                    'component': r.component,
                    'status': r.status,
                    'details': r.details,
                    'recommendations': r.recommendations,
                    'execution_time_ms': r.execution_time_ms,
                    'timestamp': r.timestamp
                }
                for r in results
            ]
            
        except ImportError:
            return [{'error': 'Enhanced monitoring system not available'}]
        except Exception as e:
            return [{'error': str(e)}]
    
    def test_alert_system(self) -> Dict[str, Any]:
        """Test alert system"""
        try:
            from enhanced_monitoring_system import get_enhanced_monitoring_instance
            enhanced_monitoring = get_enhanced_monitoring_instance()
            enhanced_monitoring.test_alert_system()
            
            return {'success': True, 'message': 'Test alert sent'}
            
        except ImportError:
            return {'success': False, 'error': 'Enhanced monitoring system not available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run(self):
        """Run the Flask dashboard server"""
        logger.info(f"🌐 Starting Health Dashboard on http://localhost:{self.port}")
        logger.info("📊 Available endpoints:")
        logger.info(f"  GET / - Dashboard UI")
        logger.info(f"  GET /api/status - Comprehensive status")
        logger.info(f"  GET /api/health - Basic health check")
        logger.info(f"  GET /api/metrics - Performance metrics")
        logger.info(f"  GET /api/alerts - Alert information")
        logger.info(f"  GET /api/diagnostics - Diagnostic results")
        logger.info(f"  POST /api/diagnostics/run - Run diagnostics")
        logger.info(f"  GET /api/baselines - Performance baselines")
        logger.info(f"  GET /api/system-info - System information")
        logger.info(f"  POST /api/test-alert - Test alert system")
        
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.port,
                debug=self.debug,
                threaded=True
            )
        except KeyboardInterrupt:
            logger.info("🛑 Dashboard server stopped by user")
        except Exception as e:
            logger.error(f"❌ Dashboard server error: {e}")
            raise

# Dashboard HTML Template
DASHBOARD_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hook Wrapper Health Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.5rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .status-healthy { background: #27ae60; }
        .status-warning { background: #f39c12; }
        .status-error { background: #e74c3c; }
        .status-unknown { background: #95a5a6; }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.5rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .metric-value {
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        .alert {
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 4px;
            border-left: 4px solid;
        }
        
        .alert-critical {
            background: #fdf2f2;
            border-color: #e74c3c;
            color: #c0392b;
        }
        
        .alert-warning {
            background: #fef9e7;
            border-color: #f39c12;
            color: #d68910;
        }
        
        .alert-info {
            background: #ebf3fd;
            border-color: #3498db;
            color: #2980b9;
        }
        
        .button {
            background: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin: 0.25rem;
        }
        
        .button:hover {
            background: #2980b9;
        }
        
        .button-danger {
            background: #e74c3c;
        }
        
        .button-danger:hover {
            background: #c0392b;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 1rem;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
        }
        
        .timestamp {
            font-size: 0.8rem;
            color: #7f8c8d;
            margin-top: 1rem;
        }
        
        .diagnostic-result {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .diagnostic-passed { border-left: 4px solid #27ae60; }
        .diagnostic-warning { border-left: 4px solid #f39c12; }
        .diagnostic-failed { border-left: 4px solid #e74c3c; }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .grid {
                grid-template-columns: 1fr;
            }
            
            .header {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 Hook Wrapper Health Dashboard</h1>
        <div class="status-indicator">
            <div id="overall-status-dot" class="status-dot status-unknown"></div>
            <span id="overall-status-text">Loading...</span>
        </div>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- System Overview -->
            <div class="card">
                <h3>📊 System Overview</h3>
                <div id="system-overview" class="loading">Loading system status...</div>
            </div>
            
            <!-- Performance Metrics -->
            <div class="card">
                <h3>⚡ Performance Metrics</h3>
                <div id="performance-metrics" class="loading">Loading performance data...</div>
            </div>
            
            <!-- Active Alerts -->
            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="active-alerts" class="loading">Loading alerts...</div>
            </div>
            
            <!-- Diagnostic Results -->
            <div class="card">
                <h3>🔧 Diagnostic Results</h3>
                <div id="diagnostic-results" class="loading">Loading diagnostics...</div>
                <button class="button" onclick="runDiagnostics()">Run Diagnostics</button>
            </div>
        </div>
        
        <!-- Performance Chart -->
        <div class="card">
            <h3>📈 Performance Trends</h3>
            <div class="chart-container">
                <canvas id="performance-chart"></canvas>
            </div>
        </div>
        
        <!-- System Resources Chart -->
        <div class="card">
            <h3>💻 System Resources</h3>
            <div class="chart-container">
                <canvas id="resources-chart"></canvas>
            </div>
        </div>
        
        <!-- Actions -->
        <div class="card">
            <h3>🛠️ Actions</h3>
            <button class="button" onclick="refreshDashboard()">Refresh Dashboard</button>
            <button class="button" onclick="testAlerts()">Test Alert System</button>
            <button class="button button-danger" onclick="downloadLogs()">Download Logs</button>
        </div>
    </div>
    
    <script>
        let performanceChart = null;
        let resourcesChart = null;
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
            initializeCharts();
            
            // Auto-refresh every 30 seconds
            setInterval(loadDashboardData, 30000);
        });
        
        async function loadDashboardData() {
            try {
                const [status, metrics, alerts, diagnostics] = await Promise.all([
                    fetch('/api/status').then(r => r.json()),
                    fetch('/api/metrics').then(r => r.json()),
                    fetch('/api/alerts').then(r => r.json()),
                    fetch('/api/diagnostics').then(r => r.json())
                ]);
                
                updateSystemOverview(status);
                updatePerformanceMetrics(metrics);
                updateActiveAlerts(alerts);
                updateDiagnosticResults(diagnostics);
                updateCharts(metrics);
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
                showError('Failed to load dashboard data');
            }
        }
        
        function updateSystemOverview(status) {
            const overallStatus = status.overall_status || 'unknown';
            const statusDot = document.getElementById('overall-status-dot');
            const statusText = document.getElementById('overall-status-text');
            
            statusDot.className = `status-dot status-${overallStatus}`;
            statusText.textContent = overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1);
            
            const overview = document.getElementById('system-overview');
            const uptime = status.uptime_seconds || 0;
            const uptimeFormatted = formatUptime(uptime);
            
            overview.innerHTML = `
                <div class="metric">
                    <span>Overall Status</span>
                    <span class="metric-value">${overallStatus}</span>
                </div>
                <div class="metric">
                    <span>Uptime</span>
                    <span class="metric-value">${uptimeFormatted}</span>
                </div>
                <div class="metric">
                    <span>Enhanced Monitoring</span>
                    <span class="metric-value">${status.enhanced_monitoring?.system_active ? 'Active' : 'Inactive'}</span>
                </div>
                <div class="timestamp">Last updated: ${new Date().toLocaleTimeString()}</div>
            `;
        }
        
        function updatePerformanceMetrics(metrics) {
            const performance = document.getElementById('performance-metrics');
            const wrapper = metrics.wrapper_performance || {};
            
            performance.innerHTML = `
                <div class="metric">
                    <span>Avg Execution Time</span>
                    <span class="metric-value">${wrapper.avg_execution_ms?.toFixed(1) || 0}ms</span>
                </div>
                <div class="metric">
                    <span>Success Rate</span>
                    <span class="metric-value">${((wrapper.success_rate || 0) * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Available API Keys</span>
                    <span class="metric-value">${metrics.credentials?.available_keys || 0}</span>
                </div>
                <div class="metric">
                    <span>CPU Usage</span>
                    <span class="metric-value">${metrics.system_resources?.cpu_percent?.toFixed(1) || 0}%</span>
                </div>
            `;
        }
        
        function updateActiveAlerts(alerts) {
            const alertsContainer = document.getElementById('active-alerts');
            const activeAlerts = alerts.active_alerts || [];
            
            if (activeAlerts.length === 0) {
                alertsContainer.innerHTML = '<div style="text-align: center; color: #27ae60;">✅ No active alerts</div>';
                return;
            }
            
            let alertsHtml = '';
            activeAlerts.forEach(alert => {
                alertsHtml += `
                    <div class="alert alert-${alert.severity}">
                        <strong>${alert.component}</strong>: ${alert.message}
                        <div style="font-size: 0.8rem; margin-top: 0.25rem;">
                            ${new Date(alert.timestamp * 1000).toLocaleString()}
                        </div>
                    </div>
                `;
            });
            
            alertsContainer.innerHTML = alertsHtml;
        }
        
        function updateDiagnosticResults(diagnostics) {
            const diagnosticsContainer = document.getElementById('diagnostic-results');
            const results = diagnostics.results || [];
            
            if (results.length === 0) {
                diagnosticsContainer.innerHTML = '<div>No diagnostic results available</div>';
                return;
            }
            
            let diagnosticsHtml = '';
            results.forEach(result => {
                const statusIcon = result.status === 'passed' ? '✅' : 
                                 result.status === 'warning' ? '⚠️' : '❌';
                
                diagnosticsHtml += `
                    <div class="diagnostic-result diagnostic-${result.status}">
                        <span>${statusIcon}</span>
                        <span>${result.diagnostic_id}</span>
                        <span style="margin-left: auto; font-size: 0.8rem;">${result.execution_time_ms?.toFixed(1) || 0}ms</span>
                    </div>
                `;
            });
            
            diagnosticsContainer.innerHTML = diagnosticsHtml + '<button class="button" onclick="runDiagnostics()">Run Diagnostics</button>';
        }
        
        function initializeCharts() {
            // Performance Chart
            const perfCtx = document.getElementById('performance-chart').getContext('2d');
            performanceChart = new Chart(perfCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Execution Time (ms)',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Success Rate (%)',
                        data: [],
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Execution Time (ms)' }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: { display: true, text: 'Success Rate (%)' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            });
            
            // Resources Chart
            const resCtx = document.getElementById('resources-chart').getContext('2d');
            resourcesChart = new Chart(resCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Used CPU', 'Free CPU', 'Used Memory', 'Free Memory'],
                    datasets: [{
                        data: [0, 100, 0, 100],
                        backgroundColor: ['#e74c3c', '#ecf0f1', '#f39c12', '#ecf0f1']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        function updateCharts(metrics) {
            const wrapper = metrics.wrapper_performance || {};
            const system = metrics.system_resources || {};
            
            // Update performance chart with mock time series data
            const now = new Date();
            performanceChart.data.labels.push(now.toLocaleTimeString());
            performanceChart.data.datasets[0].data.push(wrapper.avg_execution_ms || 0);
            performanceChart.data.datasets[1].data.push((wrapper.success_rate || 0) * 100);
            
            // Keep only last 20 data points
            if (performanceChart.data.labels.length > 20) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
                performanceChart.data.datasets[1].data.shift();
            }
            
            performanceChart.update();
            
            // Update resources chart
            const cpuUsed = system.cpu_percent || 0;
            const memUsed = system.memory_percent || 0;
            
            resourcesChart.data.datasets[0].data = [
                cpuUsed, 100 - cpuUsed,
                memUsed, 100 - memUsed
            ];
            resourcesChart.update();
        }
        
        async function runDiagnostics() {
            try {
                const response = await fetch('/api/diagnostics/run', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    showSuccess('Diagnostics completed successfully');
                    loadDashboardData(); // Refresh data
                } else {
                    showError('Diagnostics failed: ' + result.error);
                }
            } catch (error) {
                showError('Failed to run diagnostics: ' + error.message);
            }
        }
        
        async function testAlerts() {
            try {
                const response = await fetch('/api/test-alert', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    showSuccess('Test alert sent successfully');
                } else {
                    showError('Failed to send test alert: ' + result.error);
                }
            } catch (error) {
                showError('Failed to test alerts: ' + error.message);
            }
        }
        
        function refreshDashboard() {
            loadDashboardData();
            showSuccess('Dashboard refreshed');
        }
        
        function downloadLogs() {
            // This would typically download log files
            showSuccess('Log download feature coming soon');
        }
        
        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            
            if (days > 0) return `${days}d ${hours}h ${minutes}m`;
            if (hours > 0) return `${hours}h ${minutes}m`;
            return `${minutes}m`;
        }
        
        function showSuccess(message) {
            showToast(message, 'success');
        }
        
        function showError(message) {
            showToast(message, 'error');
        }
        
        function showToast(message, type) {
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 2rem;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                z-index: 1000;
                background: ${type === 'success' ? '#27ae60' : '#e74c3c'};
            `;
            toast.textContent = message;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 3000);
        }
    </script>
</body>
</html>
"""

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Health Dashboard')
    parser.add_argument('--port', type=int, default=8081, help='Port to run dashboard on (default: 8081)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    try:
        dashboard = HealthDashboard(port=args.port, debug=args.debug)
        dashboard.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Dashboard interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Dashboard failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()