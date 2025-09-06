#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///

"""
Smart API Router
================

Intelligent API routing system with automatic fallback capabilities.
Manages routing between Anthropic API direct and liteLLM proxy based on 
real-time rate limit detection and provider availability.

Features:
- Automatic fallback when primary provider is rate limited
- Session-based request queuing during rate limit periods
- Integration with existing rate_limit_parser
- Real-time observability and monitoring
- Configurable retry strategies and fallback chains
"""

import asyncio
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys
import os

# Import existing components
from utils.rate_limit_parser import RateLimitParser


@dataclass
class RoutingDecision:
    """Represents a routing decision made by the Smart API Router"""
    provider: Optional[str]
    api_type: str
    reason: str
    strategy: str  # 'primary', 'fallback', 'queue'
    confidence: float = 1.0
    estimated_delay_ms: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass 
class APIResponse:
    """Standardized API response format"""
    success: bool
    provider: str
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time_ms: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RouterConfiguration:
    """Configuration management for Smart API Router"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "primary_provider": "anthropic",
        "primary_api_type": "direct_anthropic", 
        "fallback_provider": "litellm_proxy",
        "fallback_api_type": "proxy_gemini",
        "proxy_url": "http://localhost:4001/v1",
        "observability_url": "http://localhost:4000/events",
        "queue_config": {
            "max_queue_size": 100,
            "queue_timeout_ms": 300000,  # 5 minutes
            "auto_process_interval_ms": 5000,  # 5 seconds
        },
        "retry_strategy": {
            "max_retries": 3,
            "backoff_multiplier": 2,
            "initial_delay_ms": 1000,
        },
        "health_check": {
            "interval_ms": 30000,  # 30 seconds
            "timeout_ms": 5000,    # 5 seconds
        }
    }
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize configuration manager"""
        if db_path is None:
            hooks_dir = Path(__file__).parent.parent
            db_path = hooks_dir / "rate_limits.db"
        
        self.db_path = Path(db_path)
        self._init_config_table()
        self._config_cache = {}
        self._load_config()
    
    def _init_config_table(self):
        """Initialize configuration table in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS router_configuration (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_key TEXT UNIQUE NOT NULL,
                        config_value TEXT NOT NULL,
                        updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"⚠️ Failed to initialize config table: {e}", file=sys.stderr)
    
    def _load_config(self):
        """Load configuration from database or use defaults"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT config_key, config_value FROM router_configuration")
                db_config = {row[0]: json.loads(row[1]) for row in cursor}
                
                # Merge with defaults
                self._config_cache = {**self.DEFAULT_CONFIG, **db_config}
                
        except Exception as e:
            print(f"⚠️ Failed to load config, using defaults: {e}", file=sys.stderr)
            self._config_cache = self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config_cache.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO router_configuration (config_key, config_value)
                    VALUES (?, ?)
                """, (key, json.dumps(value)))
                conn.commit()
                
                self._config_cache[key] = value
                return True
                
        except Exception as e:
            print(f"⚠️ Failed to set config {key}: {e}", file=sys.stderr)
            return False
    
    def get_endpoint_config(self, provider: str) -> Dict[str, Any]:
        """Get endpoint configuration for provider"""
        if provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_type": "direct_anthropic", 
                "endpoint": "https://api.anthropic.com/v1/messages",
                "auth_header": "x-api-key"
            }
        elif provider == "litellm_proxy":
            return {
                "provider": "litellm_proxy",
                "api_type": "proxy_gemini",
                "endpoint": f"{self.get('proxy_url')}/chat/completions",
                "auth_header": "authorization"
            }
        else:
            return {}


class SessionQueueManager:
    """Manages request queues during rate limiting periods"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_queue_table()
    
    def _init_queue_table(self):
        """Initialize session queue table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_queues (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        request_data TEXT NOT NULL,
                        queue_position INTEGER,
                        status TEXT DEFAULT 'queued',
                        priority INTEGER DEFAULT 0,
                        created_at INTEGER DEFAULT (strftime('%s', 'now')),
                        processed_at INTEGER
                    )
                """)
                
                # Create index for efficient lookups
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_queue_status 
                    ON session_queues(session_id, status, queue_position)
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"⚠️ Failed to initialize queue table: {e}", file=sys.stderr)
    
    async def enqueue_request(self, session_id: str, request_data: Dict[str, Any], priority: int = 0) -> str:
        """Add request to session queue"""
        queue_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get next queue position
                cursor = conn.execute("""
                    SELECT COALESCE(MAX(queue_position), 0) + 1 
                    FROM session_queues 
                    WHERE session_id = ? AND status = 'queued'
                """, (session_id,))
                queue_position = cursor.fetchone()[0]
                
                # Insert queued request
                conn.execute("""
                    INSERT INTO session_queues (id, session_id, request_data, queue_position, priority)
                    VALUES (?, ?, ?, ?, ?)
                """, (queue_id, session_id, json.dumps(request_data), queue_position, priority))
                
                conn.commit()
                
                print(f"📝 Request queued: {queue_id} (position {queue_position})", file=sys.stderr)
                return queue_id
                
        except Exception as e:
            print(f"⚠️ Failed to enqueue request: {e}", file=sys.stderr)
            return ""
    
    def get_queue_status(self, session_id: str) -> Dict[str, Any]:
        """Get current queue status for session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM session_queues 
                    WHERE session_id = ? 
                    GROUP BY status
                """, (session_id,))
                
                status_counts = {row[0]: row[1] for row in cursor}
                
                # Get oldest queued request
                cursor = conn.execute("""
                    SELECT created_at 
                    FROM session_queues 
                    WHERE session_id = ? AND status = 'queued'
                    ORDER BY queue_position ASC 
                    LIMIT 1
                """, (session_id,))
                
                oldest_queued = cursor.fetchone()
                oldest_age_ms = 0
                
                if oldest_queued:
                    oldest_age_ms = int((time.time() - oldest_queued[0]) * 1000)
                
                return {
                    "session_id": session_id,
                    "queued": status_counts.get("queued", 0),
                    "processing": status_counts.get("processing", 0),
                    "completed": status_counts.get("completed", 0),
                    "failed": status_counts.get("failed", 0),
                    "oldest_age_ms": oldest_age_ms
                }
                
        except Exception as e:
            print(f"⚠️ Failed to get queue status: {e}", file=sys.stderr)
            return {"session_id": session_id, "error": str(e)}
    
    async def process_queue(self, session_id: str, max_requests: int = 10) -> List[str]:
        """Process queued requests for session"""
        processed_ids = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get queued requests
                cursor = conn.execute("""
                    SELECT id, request_data 
                    FROM session_queues 
                    WHERE session_id = ? AND status = 'queued'
                    ORDER BY priority DESC, queue_position ASC
                    LIMIT ?
                """, (session_id, max_requests))
                
                queued_requests = cursor.fetchall()
                
                for queue_id, request_data_json in queued_requests:
                    try:
                        # Mark as processing
                        conn.execute("""
                            UPDATE session_queues 
                            SET status = 'processing', processed_at = strftime('%s', 'now')
                            WHERE id = ?
                        """, (queue_id,))
                        conn.commit()
                        
                        processed_ids.append(queue_id)
                        
                        # Note: Actual request processing would be handled by the router
                        # This just manages the queue state
                        
                    except Exception as e:
                        print(f"⚠️ Failed to process queue item {queue_id}: {e}", file=sys.stderr)
                        
                        # Mark as failed
                        conn.execute("""
                            UPDATE session_queues 
                            SET status = 'failed', processed_at = strftime('%s', 'now')
                            WHERE id = ?
                        """, (queue_id,))
                        conn.commit()
        
        except Exception as e:
            print(f"⚠️ Failed to process queue: {e}", file=sys.stderr)
        
        return processed_ids
    
    def cleanup_old_entries(self, max_age_hours: int = 24):
        """Clean up old queue entries"""
        cutoff_time = int(time.time()) - (max_age_hours * 3600)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM session_queues 
                    WHERE created_at < ? AND status IN ('completed', 'failed')
                """, (cutoff_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    print(f"🧹 Cleaned up {deleted_count} old queue entries", file=sys.stderr)
                    
        except Exception as e:
            print(f"⚠️ Failed to cleanup queue entries: {e}", file=sys.stderr)


class SmartAPIRouter:
    """
    Smart API Router with automatic fallback capabilities.
    
    Manages intelligent routing between multiple API providers based on:
    - Real-time rate limit detection
    - Provider availability and health
    - Session-based request queuing
    - Configurable fallback strategies
    """
    
    def __init__(self, rate_limit_parser: Optional[RateLimitParser] = None):
        """Initialize Smart API Router"""
        
        # Initialize components
        self.rate_limit_parser = rate_limit_parser or RateLimitParser()
        self.config = RouterConfiguration(self.rate_limit_parser.db_path)
        self.queue_manager = SessionQueueManager(self.rate_limit_parser.db_path)
        
        # Initialize tracking tables
        self._init_routing_table()
        
        # Runtime state
        self._provider_health = {}
        self._last_health_check = 0
        
        print("🚀 Smart API Router initialized", file=sys.stderr)
    
    def _init_routing_table(self):
        """Initialize routing decisions table"""
        try:
            with sqlite3.connect(self.rate_limit_parser.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS routing_decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        request_timestamp INTEGER NOT NULL,
                        primary_provider TEXT NOT NULL,
                        fallback_provider TEXT,
                        decision_reason TEXT,
                        route_taken TEXT NOT NULL,
                        success BOOLEAN,
                        response_time_ms INTEGER,
                        tokens_used INTEGER DEFAULT 0,
                        cost_estimate REAL DEFAULT 0.0,
                        created_at INTEGER DEFAULT (strftime('%s', 'now'))
                    )
                """)
                
                # Create index for efficient lookups
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_routing_session_timestamp 
                    ON routing_decisions(session_id, request_timestamp)
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"⚠️ Failed to initialize routing table: {e}", file=sys.stderr)
    
    async def route_request(self, request_data: Dict[str, Any], session_id: str = "unknown") -> RoutingDecision:
        """
        Intelligent routing decision based on current rate limits and provider health.
        
        Args:
            request_data: API request payload
            session_id: Session identifier for tracking
            
        Returns:
            RoutingDecision with provider selection and metadata
        """
        
        start_time = time.time()
        
        try:
            # Handle None request_data gracefully
            if request_data is None:
                return RoutingDecision(
                    provider=None,
                    api_type="error",
                    reason="Invalid request data: request_data is None",
                    strategy="error",
                    confidence=0.0,
                    metadata={"error_type": "invalid_input"}
                )
            
            # Get primary provider configuration
            primary_provider = self.config.get("primary_provider")
            primary_api_type = self.config.get("primary_api_type")
            
            print(f"🧭 Routing decision for {primary_provider}:{primary_api_type}", file=sys.stderr)
            
            # Check rate limits using existing parser
            should_fallback, recommended_fallback = self.rate_limit_parser.should_use_fallback(
                primary_provider, primary_api_type
            )
            
            if should_fallback:
                print(f"🚫 Primary provider rate limited, checking fallback", file=sys.stderr)
                
                # Get fallback provider
                fallback_provider = recommended_fallback or self.config.get("fallback_provider")
                fallback_api_type = self.config.get("fallback_api_type")
                
                # Check if fallback is also rate limited
                fallback_limited, _ = self.rate_limit_parser.should_use_fallback(
                    fallback_provider, fallback_api_type
                )
                
                if not fallback_limited:
                    # Use fallback provider
                    decision = RoutingDecision(
                        provider=fallback_provider,
                        api_type=fallback_api_type,
                        reason=f"Primary {primary_provider} rate limited, using {fallback_provider}",
                        strategy="fallback",
                        confidence=0.9,
                        metadata={
                            "primary_provider": primary_provider,
                            "fallback_reason": "rate_limited"
                        }
                    )
                else:
                    # Both providers rate limited - queue request
                    print(f"⏸️ All providers rate limited, queueing request", file=sys.stderr)
                    
                    decision = RoutingDecision(
                        provider=None,
                        api_type="queued",
                        reason="All providers rate limited, request queued",
                        strategy="queue",
                        confidence=0.5,
                        estimated_delay_ms=self._estimate_queue_delay(session_id),
                        metadata={
                            "primary_provider": primary_provider,
                            "fallback_provider": fallback_provider,
                            "queue_reason": "all_rate_limited"
                        }
                    )
            else:
                # Use primary provider
                decision = RoutingDecision(
                    provider=primary_provider,
                    api_type=primary_api_type,
                    reason="Primary provider available",
                    strategy="primary",
                    confidence=1.0,
                    metadata={
                        "provider_health": "healthy"
                    }
                )
            
            # Record routing decision
            await self._record_routing_decision(session_id, decision, start_time)
            
            print(f"📊 Routing decision: {decision.strategy} -> {decision.provider}", file=sys.stderr)
            return decision
            
        except Exception as e:
            print(f"⚠️ Error in routing decision: {e}", file=sys.stderr)
            
            # Fallback to primary provider on error
            return RoutingDecision(
                provider=self.config.get("primary_provider"),
                api_type=self.config.get("primary_api_type"),
                reason=f"Error in routing logic: {e}",
                strategy="error_fallback",
                confidence=0.3
            )
    
    async def execute_with_fallback(self, request_data: Dict[str, Any], session_id: str = "unknown") -> APIResponse:
        """
        Execute request with automatic fallback logic.
        
        Args:
            request_data: API request payload
            session_id: Session identifier
            
        Returns:
            APIResponse from successful provider
        """
        
        start_time = time.time()
        
        try:
            # Handle None request_data gracefully
            if request_data is None:
                return APIResponse(
                    success=False,
                    provider="error",
                    error="Invalid request data: request_data is None",
                    response_time_ms=int((time.time() - start_time) * 1000),
                    metadata={"error_type": "invalid_input"}
                )
            
            # Get routing decision
            routing_decision = await self.route_request(request_data, session_id)
            
            if routing_decision.strategy == "queue":
                # Enqueue request and return queue response
                queue_id = await self.queue_manager.enqueue_request(session_id, request_data)
                
                return APIResponse(
                    success=False,
                    provider="queued",
                    error="Request queued due to rate limits",
                    metadata={
                        "queue_id": queue_id,
                        "estimated_delay_ms": routing_decision.estimated_delay_ms,
                        "strategy": "queued"
                    }
                )
            
            if routing_decision.strategy == "error":
                # Return error response for invalid routing
                return APIResponse(
                    success=False,
                    provider="error",
                    error=routing_decision.reason,
                    response_time_ms=int((time.time() - start_time) * 1000),
                    metadata=routing_decision.metadata
                )
            
            # Execute request with selected provider
            provider = routing_decision.provider
            api_type = routing_decision.api_type
            
            try:
                response = await self._execute_api_request(provider, api_type, request_data)
                
                # Update routing decision with success
                await self._update_routing_decision_result(
                    session_id, routing_decision, True, 
                    int((time.time() - start_time) * 1000),
                    response.tokens_used, response.cost_estimate
                )
                
                return response
                
            except Exception as api_error:
                print(f"⚠️ API request failed for {provider}: {api_error}", file=sys.stderr)
                
                # Update routing decision with failure
                await self._update_routing_decision_result(
                    session_id, routing_decision, False,
                    int((time.time() - start_time) * 1000)
                )
                
                # If primary failed, try fallback
                if routing_decision.strategy == "primary":
                    fallback_provider = self.config.get("fallback_provider")
                    fallback_api_type = self.config.get("fallback_api_type")
                    
                    if fallback_provider:
                        print(f"🔄 Trying fallback provider: {fallback_provider}", file=sys.stderr)
                        
                        try:
                            fallback_response = await self._execute_api_request(
                                fallback_provider, fallback_api_type, request_data
                            )
                            
                            fallback_response.metadata["fallback_reason"] = "primary_failed"
                            return fallback_response
                            
                        except Exception as fallback_error:
                            print(f"⚠️ Fallback also failed: {fallback_error}", file=sys.stderr)
                
                # Return error response
                return APIResponse(
                    success=False,
                    provider=provider,
                    error=str(api_error),
                    response_time_ms=int((time.time() - start_time) * 1000)
                )
                
        except Exception as e:
            print(f"⚠️ Error in execute_with_fallback: {e}", file=sys.stderr)
            
            return APIResponse(
                success=False,
                provider="error",
                error=str(e),
                response_time_ms=int((time.time() - start_time) * 1000),
                metadata={"error_type": "execution_error"}
            )
    
    async def _execute_api_request(self, provider: str, api_type: str, request_data: Dict[str, Any]) -> APIResponse:
        """
        Execute actual API request to specified provider.
        
        Note: This is a simplified implementation. In production, this would
        contain the actual API client logic for each provider.
        """
        
        start_time = time.time()
        
        try:
            # Simulate API request based on provider
            if provider == "anthropic":
                # Simulate Anthropic API call
                await asyncio.sleep(0.1)  # Simulate network delay
                
                return APIResponse(
                    success=True,
                    provider="anthropic",
                    response_data={"response": "Simulated Anthropic response"},
                    response_time_ms=int((time.time() - start_time) * 1000),
                    tokens_used=150,
                    cost_estimate=0.003,
                    metadata={
                        "api_type": api_type,
                        "model": "claude-3-sonnet-20240229"
                    }
                )
                
            elif provider == "litellm_proxy":
                # Simulate liteLLM proxy call
                await asyncio.sleep(0.15)  # Simulate network delay
                
                return APIResponse(
                    success=True,
                    provider="litellm_proxy",
                    response_data={"response": "Simulated Gemini via liteLLM response"},
                    response_time_ms=int((time.time() - start_time) * 1000),
                    tokens_used=120,
                    cost_estimate=0.002,
                    metadata={
                        "api_type": api_type,
                        "model": "gemini-2.5-pro",
                        "proxy_url": self.config.get("proxy_url")
                    }
                )
            
            else:
                raise ValueError(f"Unknown provider: {provider}")
                
        except Exception as e:
            raise Exception(f"API request failed for {provider}: {e}")
    
    def get_routing_status(self) -> Dict[str, Any]:
        """Get current routing status for observability"""
        
        try:
            # Get current rate limits
            current_limits = self.rate_limit_parser.get_current_rate_limits()
            
            # Get queue status for recent sessions
            recent_sessions = self._get_recent_sessions(hours=1)
            queue_status = {}
            
            for session_id in recent_sessions:
                queue_status[session_id] = self.queue_manager.get_queue_status(session_id)
            
            # Get routing statistics
            routing_stats = self._get_routing_statistics(hours=24)
            
            # Determine recommendations
            recommendations = self._generate_routing_recommendations(current_limits, routing_stats)
            
            return {
                "timestamp": int(time.time() * 1000),
                "primary_provider": self.config.get("primary_provider"),
                "fallback_provider": self.config.get("fallback_provider"),
                "current_rate_limits": current_limits,
                "queue_status": queue_status,
                "routing_stats": routing_stats,
                "recommendations": recommendations,
                "should_queue": len(current_limits) >= 2,  # Both providers limited
                "health_status": self._provider_health
            }
            
        except Exception as e:
            print(f"⚠️ Error getting routing status: {e}", file=sys.stderr)
            return {
                "timestamp": int(time.time() * 1000),
                "error": str(e)
            }
    
    async def process_session_queue(self, session_id: str) -> Dict[str, Any]:
        """Process queued requests for a session"""
        
        try:
            # Check if providers are available
            routing_decision = await self.route_request({}, session_id)
            
            if routing_decision.strategy in ["primary", "fallback"]:
                # Process queue
                processed_ids = await self.queue_manager.process_queue(session_id)
                
                return {
                    "session_id": session_id,
                    "processed_count": len(processed_ids),
                    "processed_ids": processed_ids,
                    "queue_status": self.queue_manager.get_queue_status(session_id)
                }
            else:
                return {
                    "session_id": session_id,
                    "processed_count": 0,
                    "reason": "Providers still unavailable"
                }
                
        except Exception as e:
            print(f"⚠️ Error processing session queue: {e}", file=sys.stderr)
            return {
                "session_id": session_id,
                "error": str(e)
            }
    
    def _estimate_queue_delay(self, session_id: str) -> int:
        """Estimate delay for queued requests"""
        try:
            queue_status = self.queue_manager.get_queue_status(session_id)
            queued_count = queue_status.get("queued", 0)
            
            # Get rate limit info to estimate recovery time
            current_limits = self.rate_limit_parser.get_current_rate_limits()
            
            min_reset_time = float('inf')
            for limit_info in current_limits.values():
                remaining = limit_info.get("remaining_seconds", 0)
                if remaining < min_reset_time:
                    min_reset_time = remaining
            
            if min_reset_time == float('inf'):
                min_reset_time = 60  # Default 1 minute
            
            # Estimate: reset time + queue processing time
            queue_processing_time = queued_count * 2  # 2 seconds per request
            total_delay_ms = (min_reset_time + queue_processing_time) * 1000
            
            return int(total_delay_ms)
            
        except Exception:
            return 120000  # Default 2 minutes
    
    async def _record_routing_decision(self, session_id: str, decision: RoutingDecision, start_time: float):
        """Record routing decision to database"""
        try:
            with sqlite3.connect(self.rate_limit_parser.db_path) as conn:
                conn.execute("""
                    INSERT INTO routing_decisions 
                    (session_id, request_timestamp, primary_provider, fallback_provider, 
                     decision_reason, route_taken)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    int(start_time),
                    self.config.get("primary_provider"),
                    decision.metadata.get("fallback_provider"),
                    decision.reason,
                    decision.strategy
                ))
                conn.commit()
        except Exception as e:
            print(f"⚠️ Failed to record routing decision: {e}", file=sys.stderr)
    
    async def _update_routing_decision_result(self, session_id: str, decision: RoutingDecision, 
                                           success: bool, response_time_ms: int, 
                                           tokens_used: int = 0, cost_estimate: float = 0.0):
        """Update routing decision with execution results"""
        try:
            with sqlite3.connect(self.rate_limit_parser.db_path) as conn:
                # Use a subquery to find the latest record for this session and strategy
                conn.execute("""
                    UPDATE routing_decisions 
                    SET success = ?, response_time_ms = ?, tokens_used = ?, cost_estimate = ?
                    WHERE id = (
                        SELECT id FROM routing_decisions 
                        WHERE session_id = ? AND route_taken = ?
                        ORDER BY created_at DESC 
                        LIMIT 1
                    )
                """, (success, response_time_ms, tokens_used, cost_estimate, session_id, decision.strategy))
                conn.commit()
        except Exception as e:
            print(f"⚠️ Failed to update routing decision result: {e}", file=sys.stderr)
    
    def _get_recent_sessions(self, hours: int = 1) -> List[str]:
        """Get list of recent session IDs"""
        try:
            cutoff_time = int(time.time()) - (hours * 3600)
            
            with sqlite3.connect(self.rate_limit_parser.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT session_id 
                    FROM routing_decisions 
                    WHERE created_at > ?
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (cutoff_time,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"⚠️ Failed to get recent sessions: {e}", file=sys.stderr)
            return []
    
    def _get_routing_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get routing statistics for the specified time period"""
        try:
            cutoff_time = int(time.time()) - (hours * 3600)
            
            with sqlite3.connect(self.rate_limit_parser.db_path) as conn:
                # Get strategy distribution
                cursor = conn.execute("""
                    SELECT route_taken, COUNT(*) as count, 
                           AVG(response_time_ms) as avg_response_time,
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                    FROM routing_decisions 
                    WHERE created_at > ?
                    GROUP BY route_taken
                """, (cutoff_time,))
                
                strategy_stats = {}
                for row in cursor.fetchall():
                    strategy, count, avg_time, success_count = row
                    strategy_stats[strategy] = {
                        "count": count,
                        "success_rate": success_count / count if count > 0 else 0,
                        "avg_response_time_ms": int(avg_time) if avg_time else 0
                    }
                
                # Get total statistics
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_requests,
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as total_success,
                           AVG(response_time_ms) as avg_response_time,
                           SUM(tokens_used) as total_tokens,
                           SUM(cost_estimate) as total_cost
                    FROM routing_decisions 
                    WHERE created_at > ?
                """, (cutoff_time,))
                
                totals = cursor.fetchone()
                
                return {
                    "time_period_hours": hours,
                    "strategy_distribution": strategy_stats,
                    "totals": {
                        "requests": totals[0] if totals[0] else 0,
                        "success_rate": totals[1] / totals[0] if totals[0] > 0 else 0,
                        "avg_response_time_ms": int(totals[2]) if totals[2] else 0,
                        "total_tokens": totals[3] if totals[3] else 0,
                        "total_cost": totals[4] if totals[4] else 0.0
                    }
                }
                
        except Exception as e:
            print(f"⚠️ Failed to get routing statistics: {e}", file=sys.stderr)
            return {"error": str(e)}
    
    def _generate_routing_recommendations(self, current_limits: Dict, routing_stats: Dict) -> List[str]:
        """Generate routing recommendations based on current state"""
        recommendations = []
        
        try:
            # Check rate limit status
            if len(current_limits) > 0:
                recommendations.append("Rate limits detected - automatic fallback active")
            
            # Check success rates
            if "strategy_distribution" in routing_stats:
                for strategy, stats in routing_stats["strategy_distribution"].items():
                    success_rate = stats.get("success_rate", 0)
                    if success_rate < 0.8:
                        recommendations.append(f"Low success rate for {strategy} strategy: {success_rate:.1%}")
            
            # Check response times
            if "totals" in routing_stats:
                avg_time = routing_stats["totals"].get("avg_response_time_ms", 0)
                if avg_time > 5000:
                    recommendations.append(f"High average response time: {avg_time}ms")
            
            if not recommendations:
                recommendations.append("System operating normally")
                
        except Exception as e:
            recommendations.append(f"Error generating recommendations: {e}")
        
        return recommendations


def create_smart_router() -> SmartAPIRouter:
    """Factory function to create a Smart API Router instance"""
    return SmartAPIRouter()


async def test_smart_router():
    """Test function for Smart API Router"""
    print("🧪 Testing Smart API Router")
    print("=" * 50)
    
    # Create router
    router = create_smart_router()
    
    # Test routing decision
    test_request = {"model": "claude-3-sonnet", "message": "Hello, world!"}
    session_id = "test_session_" + str(int(time.time()))
    
    print(f"📝 Testing routing decision for session: {session_id}")
    decision = await router.route_request(test_request, session_id)
    print(f"   Decision: {decision.strategy} -> {decision.provider}")
    print(f"   Reason: {decision.reason}")
    print(f"   Confidence: {decision.confidence}")
    
    # Test execution
    print(f"\n🚀 Testing request execution")
    response = await router.execute_with_fallback(test_request, session_id)
    print(f"   Success: {response.success}")
    print(f"   Provider: {response.provider}")
    print(f"   Response Time: {response.response_time_ms}ms")
    
    # Test routing status
    print(f"\n📊 Testing routing status")
    status = router.get_routing_status()
    print(f"   Primary Provider: {status.get('primary_provider')}")
    print(f"   Rate Limits: {len(status.get('current_rate_limits', {}))}")
    print(f"   Recommendations: {len(status.get('recommendations', []))}")
    
    # Test queue management
    print(f"\n📋 Testing queue management")
    queue_status = router.queue_manager.get_queue_status(session_id)
    print(f"   Queue Status: {queue_status}")
    
    print(f"\n✅ Smart API Router test completed")


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_smart_router())