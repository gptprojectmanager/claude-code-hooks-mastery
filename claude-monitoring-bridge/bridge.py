#!/usr/bin/env python3
"""
Claude Monitoring Bridge - OPZIONE C Hybrid Bridge Implementation
Connects Usage Monitor CLI with Hooks System for unified monitoring and auto-recovery
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
import websockets
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

class ClaudeMonitoringBridge:
    """Core bridge component connecting Usage Monitor and Hooks System"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # State management
        self.websocket_connection = None
        self.last_usage_data = {}
        self.last_hooks_data = {}
        self.alerts_active = {}
        self.recovery_state = "normal"  # normal, paused, recovering
        
        # FastAPI app for REST API
        self.app = FastAPI(title="Claude Monitoring Bridge", version="1.0.0")
        self._setup_api_routes()
        
        self.logger.info("Claude Monitoring Bridge initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file {config_path} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format=self.config['logging']['format'],
            handlers=[
                logging.FileHandler(self.config['logging']['file']),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def connect_to_bun_server(self):
        """Establish WebSocket connection to Bun server"""
        config = self.config['integration']['bun_server']
        uri = f"ws://{config['host']}:{config['port']}{config['websocket_endpoint']}"
        
        max_attempts = config['reconnect_attempts']
        delay = config['reconnect_delay']
        
        for attempt in range(max_attempts):
            try:
                self.websocket_connection = await websockets.connect(uri)
                self.logger.info(f"Connected to Bun server at {uri}")
                return True
            except Exception as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
        
        self.logger.error(f"Failed to connect to Bun server after {max_attempts} attempts")
        return False
    
    async def listen_to_hooks_events(self):
        """Listen to WebSocket events from hooks system"""
        if not self.websocket_connection:
            self.logger.error("No WebSocket connection available")
            return
        
        try:
            async for message in self.websocket_connection:
                try:
                    data = json.loads(message)
                    self.last_hooks_data = data
                    self.logger.debug(f"Received hooks event: {data.get('event_type', 'unknown')}")
                    
                    # Process hooks data for alerts
                    await self._process_hooks_event(data)
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON received: {message}")
                except Exception as e:
                    self.logger.error(f"Error processing hooks event: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            # Attempt reconnection
            await self.connect_to_bun_server()
    
    async def poll_usage_monitor(self):
        """Poll Usage Monitor CLI for metrics"""
        config = self.config['integration']['usage_monitor']
        poll_interval = config['poll_interval']
        
        while True:
            try:
                # Execute claude-monitor CLI
                cmd = config['cli_command'].split()  # Split command (no JSON option available)
                result = subprocess.run(
                    cmd, 
                    cwd=config['cli_path'],
                    capture_output=True, 
                    text=True,
                    timeout=config['timeout']
                )
                
                if result.returncode == 0:
                    try:
                        self.last_usage_data = json.loads(result.stdout)
                        self.logger.debug("Usage Monitor data updated")
                        
                        # Process usage data for alerts
                        await self._process_usage_data(self.last_usage_data)
                        
                    except json.JSONDecodeError:
                        # Fallback: parse text output
                        self.last_usage_data = {"raw_output": result.stdout}
                        self.logger.debug("Usage Monitor raw output captured")
                else:
                    self.logger.warning(f"Usage Monitor CLI failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.logger.warning("Usage Monitor CLI timeout")
            except Exception as e:
                self.logger.error(f"Error polling Usage Monitor: {e}")
            
            await asyncio.sleep(poll_interval)
    
    async def _process_hooks_event(self, event_data: Dict[str, Any]):
        """Process hooks system events for alert triggers"""
        event_type = event_data.get('event_type')
        
        if event_type == 'RateLimitApproaching':
            await self._trigger_alert('rate_limit', event_data)
        elif event_type == 'SessionTimeout':
            await self._trigger_alert('time_limit', event_data)
        elif event_type == 'HighTokenUsage':
            await self._trigger_alert('token_usage', event_data)
    
    async def _process_usage_data(self, usage_data: Dict[str, Any]):
        """Process Usage Monitor data for alert triggers"""
        # Check token threshold
        if 'token_usage_percent' in usage_data:
            if usage_data['token_usage_percent'] > self.config['alerts']['token_threshold']:
                await self._trigger_alert('token_threshold', usage_data)
        
        # Check cost threshold
        if 'total_cost' in usage_data:
            if usage_data['total_cost'] > self.config['alerts']['cost_threshold']:
                await self._trigger_alert('cost_threshold', usage_data)
    
    async def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger alert and potentially initiate recovery"""
        if alert_type in self.alerts_active:
            return  # Alert already active
        
        self.alerts_active[alert_type] = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        self.logger.warning(f"ALERT: {alert_type} triggered")
        
        # Auto-recovery logic
        if self.config['recovery']['auto_recovery']:
            await self._initiate_recovery(alert_type, data)
    
    async def _initiate_recovery(self, alert_type: str, data: Dict[str, Any]):
        """Initiate appropriate recovery strategy"""
        recovery_config = self.config['recovery']
        
        if alert_type == 'rate_limit' and recovery_config['rate_limit'] == 'exponential_backoff':
            await self._exponential_backoff_recovery()
        elif alert_type == 'time_limit' and recovery_config['time_limit'] == 'session_pause':
            await self._session_pause_recovery()
        elif alert_type in ['cost_threshold', 'token_threshold']:
            await self._graceful_degradation_recovery()
    
    async def _exponential_backoff_recovery(self):
        """Implement exponential backoff recovery strategy"""
        self.recovery_state = "recovering"
        self.logger.info("Initiating exponential backoff recovery")
        
        delays = [1, 2, 4, 8, 16, 32]  # seconds
        
        for delay in delays:
            self.logger.info(f"Waiting {delay} seconds before retry...")
            await asyncio.sleep(delay)
            
            # Check if recovery condition is met
            if await self._check_recovery_condition():
                self.recovery_state = "normal"
                self.logger.info("Recovery successful")
                return
        
        self.logger.error("Recovery failed after all attempts")
        self.recovery_state = "failed"
    
    async def _session_pause_recovery(self):
        """Implement session pause recovery strategy"""
        self.recovery_state = "paused"
        self.logger.info("Session paused due to time limit")
        
        # Calculate resume time (next day or when limit resets)
        resume_time = datetime.now() + timedelta(hours=24)  # Simplified logic
        
        self.logger.info(f"Session will resume at {resume_time}")
        
        # In a real implementation, this would integrate with the Claude Code session management
        # For now, just log the pause
        await asyncio.sleep(60)  # Wait 1 minute as demo
        
        self.recovery_state = "normal"
        self.logger.info("Session resumed")
    
    async def _graceful_degradation_recovery(self):
        """Implement graceful degradation recovery strategy"""
        self.recovery_state = "degraded"
        self.logger.info("Entering graceful degradation mode")
        
        # Implement reduced functionality mode
        # This would typically involve reducing agent activity, simplifying responses, etc.
        await asyncio.sleep(10)  # Simplified delay
        
        self.recovery_state = "normal"
        self.logger.info("Normal operation resumed")
    
    async def _check_recovery_condition(self) -> bool:
        """Check if recovery conditions are met"""
        # Simplified check - in reality would verify rate limits, token availability, etc.
        return True
    
    def _setup_api_routes(self):
        """Setup FastAPI routes for REST API"""
        
        @self.app.get("/")
        async def get_root():
            """Get API information and available endpoints"""
            return JSONResponse({
                "service": "Claude Monitoring Bridge",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "health": "/health",
                    "metrics": "/metrics", 
                    "alerts": "/alerts/{type}",
                    "recovery": "/recovery/status"
                },
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get unified metrics from both systems"""
            return JSONResponse({
                "timestamp": datetime.now().isoformat(),
                "hooks_data": self.last_hooks_data,
                "usage_data": self.last_usage_data,
                "recovery_state": self.recovery_state,
                "active_alerts": self.alerts_active
            })
        
        @self.app.get("/health")
        async def get_health():
            """Get system health status"""
            websocket_status = "connected" if self.websocket_connection else "disconnected"
            
            return JSONResponse({
                "status": "healthy" if websocket_status == "connected" else "degraded",
                "websocket": websocket_status,
                "recovery_state": self.recovery_state,
                "alerts_count": len(self.alerts_active),
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.post("/alerts/{alert_type}")
        async def trigger_manual_alert(alert_type: str):
            """Manually trigger an alert for testing"""
            await self._trigger_alert(alert_type, {"manual": True})
            return JSONResponse({"message": f"Alert {alert_type} triggered manually"})
        
        @self.app.get("/recovery/status")
        async def get_recovery_status():
            """Get current recovery status"""
            return JSONResponse({
                "state": self.recovery_state,
                "active_alerts": self.alerts_active,
                "timestamp": datetime.now().isoformat()
            })
    
    async def run(self):
        """Main execution loop"""
        self.logger.info("Starting Claude Monitoring Bridge")
        
        # Start tasks concurrently
        tasks = [
            asyncio.create_task(self.connect_to_bun_server()),
            asyncio.create_task(self.poll_usage_monitor()),
        ]
        
        # Wait for WebSocket connection
        await tasks[0]
        
        if self.websocket_connection:
            # Add WebSocket listener task
            tasks.append(asyncio.create_task(self.listen_to_hooks_events()))
        
        # Start FastAPI server in background
        config_api = self.config['api']
        api_task = asyncio.create_task(
            self._run_api_server(config_api['host'], config_api['port'])
        )
        tasks.append(api_task)
        
        # Run all tasks
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Bridge shutdown requested")
        except Exception as e:
            self.logger.error(f"Bridge error: {e}")
        finally:
            await self._cleanup()
    
    async def _run_api_server(self, host: str, port: int):
        """Run FastAPI server"""
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    
    async def _cleanup(self):
        """Cleanup resources"""
        if self.websocket_connection:
            await self.websocket_connection.close()
        self.logger.info("Bridge cleanup completed")


async def main():
    """Main entry point"""
    bridge = ClaudeMonitoringBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())