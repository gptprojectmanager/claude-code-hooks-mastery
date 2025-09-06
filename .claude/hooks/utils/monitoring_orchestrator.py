#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "psutil",
# ]
# ///

"""
Monitoring Orchestrator for Hook Wrapper Infrastructure
=======================================================

This module orchestrates all monitoring components and provides a unified
interface for starting, stopping, and managing the comprehensive monitoring
system for the hook wrapper infrastructure.

Key Features:
- Unified start/stop control for all monitoring components
- Health check coordination
- Service dependency management
- Configuration management
- Status reporting and aggregation
- Automatic recovery procedures

Components Managed:
- Enhanced Monitoring System
- Health Check Server
- Comprehensive Health Dashboard
- Observability System Integration
- Alert Management
- Diagnostic Automation

Usage:
    python monitoring_orchestrator.py --start-all
    python monitoring_orchestrator.py --status
    python monitoring_orchestrator.py --stop-all
"""

import os
import sys
import time
import json
import logging
import subprocess
import threading
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests

# Setup logging
log_dir = Path.home() / ".claude" / "logs" / "monitoring_orchestrator"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"orchestrator_{time.strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('monitoring_orchestrator')

class ServiceManager:
    """Manages individual monitoring service lifecycle"""
    
    def __init__(self, name: str, start_command: List[str], health_check_url: Optional[str] = None,
                 working_directory: Optional[str] = None, startup_timeout: int = 30):
        self.name = name
        self.start_command = start_command
        self.health_check_url = health_check_url
        self.working_directory = working_directory
        self.startup_timeout = startup_timeout
        
        self.process = None
        self.status = "stopped"
        self.start_time = None
        self.last_health_check = None
        
        logger.info(f"🔧 ServiceManager initialized for {name}")
    
    def start(self) -> bool:
        """Start the service"""
        if self.process and self.process.poll() is None:
            logger.warning(f"⚠️ Service {self.name} is already running")
            return True
        
        try:
            logger.info(f"🚀 Starting service: {self.name}")
            logger.debug(f"Command: {' '.join(self.start_command)}")
            
            # Start the process
            self.process = subprocess.Popen(
                self.start_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.working_directory,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.start_time = time.time()
            self.status = "starting"
            
            # Wait for service to be ready
            if self.health_check_url:
                ready = self._wait_for_health_check()
                if ready:
                    self.status = "running"
                    logger.info(f"✅ Service {self.name} started successfully")
                    return True
                else:
                    self.status = "failed"
                    logger.error(f"❌ Service {self.name} failed health check")
                    self.stop()
                    return False
            else:
                # No health check, assume success if process is running
                time.sleep(2)  # Give it a moment to start
                if self.process.poll() is None:
                    self.status = "running"
                    logger.info(f"✅ Service {self.name} started (no health check)")
                    return True
                else:
                    self.status = "failed"
                    logger.error(f"❌ Service {self.name} process exited")
                    return False
                    
        except Exception as e:
            self.status = "failed"
            logger.error(f"❌ Failed to start service {self.name}: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the service"""
        if not self.process:
            logger.info(f"ℹ️ Service {self.name} is not running")
            return True
        
        try:
            logger.info(f"🛑 Stopping service: {self.name}")
            
            # Try graceful shutdown first
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning(f"⚠️ Force killing service {self.name}")
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait()
            
            self.process = None
            self.status = "stopped"
            logger.info(f"✅ Service {self.name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop service {self.name}: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart the service"""
        logger.info(f"🔄 Restarting service: {self.name}")
        self.stop()
        time.sleep(2)  # Brief pause between stop and start
        return self.start()
    
    def check_health(self) -> bool:
        """Check service health"""
        if not self.health_check_url:
            # If no health check URL, just check if process is running
            if self.process and self.process.poll() is None:
                self.last_health_check = time.time()
                return True
            else:
                return False
        
        try:
            response = requests.get(self.health_check_url, timeout=5)
            healthy = response.status_code == 200
            self.last_health_check = time.time()
            
            if not healthy:
                logger.warning(f"⚠️ Service {self.name} health check failed: HTTP {response.status_code}")
            
            return healthy
            
        except Exception as e:
            logger.warning(f"⚠️ Service {self.name} health check error: {e}")
            return False
    
    def _wait_for_health_check(self) -> bool:
        """Wait for service to pass health check"""
        if not self.health_check_url:
            return True
        
        start_time = time.time()
        while time.time() - start_time < self.startup_timeout:
            try:
                response = requests.get(self.health_check_url, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            
            time.sleep(1)
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            'name': self.name,
            'status': self.status,
            'uptime_seconds': uptime,
            'pid': self.process.pid if self.process else None,
            'health_check_url': self.health_check_url,
            'last_health_check': self.last_health_check,
            'healthy': self.check_health() if self.status == "running" else False
        }

class MonitoringOrchestrator:
    """Main orchestrator for all monitoring components"""
    
    def __init__(self):
        self.services = {}
        self.config = self._load_config()
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Initialize service managers
        self._initialize_services()
        
        logger.info("🎯 MonitoringOrchestrator initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration"""
        config_file = Path.home() / ".claude" / "monitoring" / "orchestrator_config.json"
        
        default_config = {
            'health_check_interval': 30,
            'auto_restart_failed_services': True,
            'startup_order': [
                'observability_system',
                'enhanced_monitoring',
                'health_check_server',
                'health_dashboard'
            ],
            'dependencies': {
                'enhanced_monitoring': ['observability_system'],
                'health_check_server': ['enhanced_monitoring'],
                'health_dashboard': ['enhanced_monitoring', 'health_check_server']
            },
            'ports': {
                'observability_server': 4000,
                'observability_client': 5173,
                'health_check_server': 8080,
                'health_dashboard': 8081
            }
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                logger.info("✅ Loaded orchestrator configuration")
            else:
                # Create default config
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info("📋 Created default orchestrator configuration")
                
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
        
        return default_config
    
    def _initialize_services(self):
        """Initialize all service managers"""
        
        # Get project root
        project_root = Path(__file__).parent.parent.parent.parent
        hooks_dir = Path(__file__).parent
        
        # Observability System (already managed by existing startup hook)
        # We'll just check its health, not manage its lifecycle
        self.services['observability_system'] = ServiceManager(
            name='observability_system',
            start_command=[],  # Empty - managed externally
            health_check_url=f"http://localhost:{self.config['ports']['observability_server']}/health"
        )
        
        # Enhanced Monitoring System
        self.services['enhanced_monitoring'] = ServiceManager(
            name='enhanced_monitoring',
            start_command=[
                'uv', 'run', str(hooks_dir / 'enhanced_monitoring_system.py'), '--start', '--daemon'
            ],
            working_directory=str(hooks_dir)
        )
        
        # Health Check Server
        self.services['health_check_server'] = ServiceManager(
            name='health_check_server',
            start_command=[
                'uv', 'run', str(hooks_dir / 'health_check_server.py'),
                '--port', str(self.config['ports']['health_check_server'])
            ],
            health_check_url=f"http://localhost:{self.config['ports']['health_check_server']}/ping",
            working_directory=str(hooks_dir)
        )
        
        # Health Dashboard
        self.services['health_dashboard'] = ServiceManager(
            name='health_dashboard',
            start_command=[
                'uv', 'run', str(hooks_dir / 'comprehensive_health_dashboard.py'),
                '--port', str(self.config['ports']['health_dashboard'])
            ],
            health_check_url=f"http://localhost:{self.config['ports']['health_dashboard']}/api/health",
            working_directory=str(hooks_dir)
        )
        
        logger.info(f"🔧 Initialized {len(self.services)} service managers")
    
    def start_all_services(self) -> bool:
        """Start all monitoring services in dependency order"""
        logger.info("🚀 Starting all monitoring services")
        
        success = True
        startup_order = self.config['startup_order']
        
        for service_name in startup_order:
            if service_name not in self.services:
                logger.warning(f"⚠️ Unknown service in startup order: {service_name}")
                continue
            
            # Check dependencies
            dependencies = self.config['dependencies'].get(service_name, [])
            deps_ready = self._check_dependencies(dependencies)
            
            if not deps_ready:
                logger.error(f"❌ Dependencies not ready for {service_name}")
                success = False
                continue
            
            # Start the service
            if service_name == 'observability_system':
                # Special handling for observability system
                if not self._check_observability_system():
                    logger.error("❌ Observability system is not running")
                    success = False
                else:
                    logger.info("✅ Observability system is already running")
            else:
                service = self.services[service_name]
                if not service.start():
                    success = False
            
            # Brief pause between service starts
            time.sleep(2)
        
        if success:
            logger.info("✅ All monitoring services started successfully")
            self._start_health_monitoring()
        else:
            logger.error("❌ Some services failed to start")
        
        return success
    
    def stop_all_services(self) -> bool:
        """Stop all monitoring services"""
        logger.info("🛑 Stopping all monitoring services")
        
        self._stop_health_monitoring()
        
        success = True
        # Stop in reverse order
        startup_order = list(reversed(self.config['startup_order']))
        
        for service_name in startup_order:
            if service_name == 'observability_system':
                logger.info("ℹ️ Observability system managed externally, skipping stop")
                continue
            
            if service_name in self.services:
                service = self.services[service_name]
                if not service.stop():
                    success = False
            
            time.sleep(1)
        
        if success:
            logger.info("✅ All monitoring services stopped successfully")
        else:
            logger.error("❌ Some services failed to stop cleanly")
        
        return success
    
    def restart_all_services(self) -> bool:
        """Restart all monitoring services"""
        logger.info("🔄 Restarting all monitoring services")
        self.stop_all_services()
        time.sleep(5)  # Longer pause for restart
        return self.start_all_services()
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        if service_name not in self.services:
            logger.error(f"❌ Unknown service: {service_name}")
            return False
        
        if service_name == 'observability_system':
            logger.warning("⚠️ Cannot restart observability system (managed externally)")
            return False
        
        service = self.services[service_name]
        return service.restart()
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all monitoring services"""
        
        status = {
            'orchestrator': {
                'active': True,
                'monitoring_active': self.monitoring_active,
                'timestamp': time.time(),
                'configuration': self.config
            },
            'services': {},
            'overall_health': 'unknown',
            'summary': {
                'total_services': len(self.services),
                'running_services': 0,
                'healthy_services': 0,
                'failed_services': 0
            }
        }
        
        # Get status for each service
        running = 0
        healthy = 0
        failed = 0
        
        for service_name, service in self.services.items():
            service_status = service.get_status()
            status['services'][service_name] = service_status
            
            if service_status['status'] == 'running':
                running += 1
                if service_status['healthy']:
                    healthy += 1
            elif service_status['status'] == 'failed':
                failed += 1
        
        # Special handling for observability system
        if 'observability_system' in status['services']:
            obs_status = status['services']['observability_system']
            if self._check_observability_system():
                obs_status['status'] = 'running'
                obs_status['healthy'] = True
                running += 1
                healthy += 1
            else:
                obs_status['status'] = 'stopped'
                obs_status['healthy'] = False
        
        # Update summary
        status['summary']['running_services'] = running
        status['summary']['healthy_services'] = healthy
        status['summary']['failed_services'] = failed
        
        # Determine overall health
        if failed > 0:
            status['overall_health'] = 'critical'
        elif running == len(self.services) and healthy == running:
            status['overall_health'] = 'healthy'
        elif running > len(self.services) / 2:
            status['overall_health'] = 'degraded'
        else:
            status['overall_health'] = 'critical'
        
        return status
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if service dependencies are ready"""
        for dep in dependencies:
            if dep not in self.services:
                logger.warning(f"⚠️ Unknown dependency: {dep}")
                continue
            
            if dep == 'observability_system':
                if not self._check_observability_system():
                    return False
            else:
                service = self.services[dep]
                if service.status != 'running' or not service.check_health():
                    return False
        
        return True
    
    def _check_observability_system(self) -> bool:
        """Check if observability system is running"""
        try:
            response = requests.get(
                f"http://localhost:{self.config['ports']['observability_server']}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def _start_health_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        def health_monitor():
            logger.info("🔍 Health monitoring started")
            self.monitoring_active = True
            
            while self.monitoring_active:
                try:
                    self._perform_health_checks()
                    time.sleep(self.config['health_check_interval'])
                except Exception as e:
                    logger.error(f"❌ Error in health monitoring: {e}")
                    time.sleep(self.config['health_check_interval'])
            
            logger.info("🛑 Health monitoring stopped")
        
        self.monitoring_thread = threading.Thread(target=health_monitor, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🚀 Health monitoring started")
    
    def _stop_health_monitoring(self):
        """Stop continuous health monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("✅ Health monitoring stopped")
    
    def _perform_health_checks(self):
        """Perform health checks on all services"""
        for service_name, service in self.services.items():
            if service.status != 'running':
                continue
            
            healthy = service.check_health()
            
            if not healthy and self.config['auto_restart_failed_services']:
                logger.warning(f"⚠️ Service {service_name} is unhealthy, attempting restart")
                
                # Try to restart the service
                if service_name != 'observability_system':
                    restart_success = service.restart()
                    if restart_success:
                        logger.info(f"✅ Service {service_name} restarted successfully")
                    else:
                        logger.error(f"❌ Failed to restart service {service_name}")
    
    def run_comprehensive_diagnostic(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic across all monitoring components"""
        logger.info("🔧 Running comprehensive diagnostic")
        
        diagnostic_results = {
            'timestamp': time.time(),
            'orchestrator_status': 'healthy',
            'service_diagnostics': {},
            'integration_tests': {},
            'recommendations': []
        }
        
        # Check each service
        for service_name, service in self.services.items():
            service_status = service.get_status()
            
            diagnostic_results['service_diagnostics'][service_name] = {
                'status': service_status['status'],
                'healthy': service_status['healthy'],
                'uptime': service_status['uptime_seconds'],
                'issues': []
            }
            
            # Check for issues
            if service_status['status'] != 'running':
                diagnostic_results['service_diagnostics'][service_name]['issues'].append(
                    f"Service is not running (status: {service_status['status']})"
                )
            
            if not service_status['healthy']:
                diagnostic_results['service_diagnostics'][service_name]['issues'].append(
                    "Service health check is failing"
                )
        
        # Integration tests
        try:
            # Test observability integration
            obs_response = requests.get(
                f"http://localhost:{self.config['ports']['observability_server']}/health",
                timeout=5
            )
            diagnostic_results['integration_tests']['observability'] = {
                'status': 'passed' if obs_response.status_code == 200 else 'failed',
                'response_time_ms': obs_response.elapsed.total_seconds() * 1000,
                'details': obs_response.json() if obs_response.status_code == 200 else None
            }
        except Exception as e:
            diagnostic_results['integration_tests']['observability'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test health dashboard
        try:
            dash_response = requests.get(
                f"http://localhost:{self.config['ports']['health_dashboard']}/api/health",
                timeout=5
            )
            diagnostic_results['integration_tests']['health_dashboard'] = {
                'status': 'passed' if dash_response.status_code == 200 else 'failed',
                'response_time_ms': dash_response.elapsed.total_seconds() * 1000,
                'details': dash_response.json() if dash_response.status_code == 200 else None
            }
        except Exception as e:
            diagnostic_results['integration_tests']['health_dashboard'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Generate recommendations
        failed_services = [
            name for name, diag in diagnostic_results['service_diagnostics'].items()
            if diag['status'] != 'running' or not diag['healthy']
        ]
        
        if failed_services:
            diagnostic_results['recommendations'].append(
                f"Restart failed services: {', '.join(failed_services)}"
            )
        
        failed_integrations = [
            name for name, test in diagnostic_results['integration_tests'].items()
            if test['status'] == 'failed'
        ]
        
        if failed_integrations:
            diagnostic_results['recommendations'].append(
                f"Fix integration issues: {', '.join(failed_integrations)}"
            )
        
        # Overall status
        if failed_services or failed_integrations:
            diagnostic_results['orchestrator_status'] = 'degraded' if len(failed_services) <= 1 else 'critical'
        
        logger.info("✅ Comprehensive diagnostic completed")
        return diagnostic_results

# Global orchestrator instance
_orchestrator_instance = None

def get_orchestrator_instance() -> MonitoringOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MonitoringOrchestrator()
    return _orchestrator_instance

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring Orchestrator')
    parser.add_argument('--start-all', action='store_true', help='Start all monitoring services')
    parser.add_argument('--stop-all', action='store_true', help='Stop all monitoring services')
    parser.add_argument('--restart-all', action='store_true', help='Restart all monitoring services')
    parser.add_argument('--restart-service', help='Restart specific service')
    parser.add_argument('--status', action='store_true', help='Show comprehensive status')
    parser.add_argument('--diagnostic', action='store_true', help='Run comprehensive diagnostic')
    parser.add_argument('--monitor', action='store_true', help='Start and monitor (stay running)')
    
    args = parser.parse_args()
    
    orchestrator = get_orchestrator_instance()
    
    try:
        if args.start_all:
            success = orchestrator.start_all_services()
            sys.exit(0 if success else 1)
        
        elif args.stop_all:
            success = orchestrator.stop_all_services()
            sys.exit(0 if success else 1)
        
        elif args.restart_all:
            success = orchestrator.restart_all_services()
            sys.exit(0 if success else 1)
        
        elif args.restart_service:
            success = orchestrator.restart_service(args.restart_service)
            sys.exit(0 if success else 1)
        
        elif args.status:
            status = orchestrator.get_comprehensive_status()
            print(json.dumps(status, indent=2, default=str))
        
        elif args.diagnostic:
            results = orchestrator.run_comprehensive_diagnostic()
            print(json.dumps(results, indent=2, default=str))
        
        elif args.monitor:
            # Start all services and keep monitoring
            success = orchestrator.start_all_services()
            if success:
                try:
                    print("🔍 Monitoring active. Press Ctrl+C to stop...")
                    signal.pause()
                except KeyboardInterrupt:
                    print("\n🛑 Stopping all services...")
                    orchestrator.stop_all_services()
            sys.exit(0 if success else 1)
        
        else:
            # Default: show brief status
            status = orchestrator.get_comprehensive_status()
            print("🎯 Monitoring Orchestrator Status:")
            print(f"  Overall Health: {status['overall_health']}")
            print(f"  Running Services: {status['summary']['running_services']}/{status['summary']['total_services']}")
            print(f"  Healthy Services: {status['summary']['healthy_services']}")
            print("\nServices:")
            for name, service_status in status['services'].items():
                status_emoji = "✅" if service_status['healthy'] else "⚠️" if service_status['status'] == 'running' else "❌"
                print(f"  {status_emoji} {name}: {service_status['status']}")
    
    except KeyboardInterrupt:
        logger.info("🛑 Orchestrator interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Orchestrator error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()