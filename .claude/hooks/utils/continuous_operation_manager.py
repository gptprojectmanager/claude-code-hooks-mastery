#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///

"""
Continuous Operation Manager
============================

24h Continuous Operation Manager for Claude Code hooks system that ensures 
continuous operation even during rate limiting periods through intelligent 
session management and auto-resume capabilities.

Features:
- Composition wrapper around existing SmartAPIRouter
- Background timer system for auto-resume after rate limits
- Thread-safe session state management
- Persistent session tracking with SQLite storage
- Integration with existing rate limit detection system
"""

import asyncio
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import sys
import os

# Import existing components
from utils.smart_api_router import SmartAPIRouter


class SessionState(Enum):
    """Session state enumeration for lifecycle management"""
    ACTIVE = 'active'
    PAUSED = 'paused'
    RATE_LIMITED = 'rate_limited'
    INTERRUPTED = 'interrupted'
    FAILED = 'failed'
    SCHEDULED_RESUME = 'scheduled_resume'
    RESTARTING = 'restarting'
    ERROR = 'error'


@dataclass
class SessionInfo:
    """Session information container"""
    session_id: str
    state: SessionState
    last_activity: float
    scheduled_resume: Optional[float] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ContinuousOperationManager:
    """
    24h Continuous Operation Manager that wraps SmartAPIRouter
    with continuous operation capabilities for rate limit resilience.
    """
    
    # Configuration constants
    MAX_RETRIES = 5
    BASE_RETRY_DELAY = 60  # seconds
    MAX_RETRY_DELAY = 300  # 5 minutes
    HEALTH_CHECK_INTERVAL = 30  # seconds
    TIMER_CHECK_INTERVAL = 5  # seconds
    
    def __init__(self, smart_router: SmartAPIRouter):
        """
        Initialize Continuous Operation Manager.
        
        Args:
            smart_router: Existing SmartAPIRouter instance to wrap
        """
        self.router = smart_router
        self.db_path = smart_router.rate_limit_parser.db_path
        
        # Session management
        self.session_states: Dict[str, SessionInfo] = {}
        self.background_timers: Dict[str, threading.Timer] = {}
        
        # Thread management
        self._running = False
        self._background_thread: Optional[threading.Thread] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.RLock()
        
        # Initialize database schema
        self._init_session_state_table()
        
        # Load existing session states
        self._load_session_states()
    
    def _init_session_state_table(self):
        """Initialize session state table in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_states (
                        session_id TEXT PRIMARY KEY,
                        state TEXT NOT NULL,
                        last_activity REAL NOT NULL,
                        scheduled_resume REAL,
                        retry_count INTEGER DEFAULT 0,
                        metadata TEXT,
                        created_at REAL DEFAULT (julianday('now') * 86400),
                        updated_at REAL DEFAULT (julianday('now') * 86400)
                    )
                """)
                
                # Create index for efficient scheduled resume lookups
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_resume 
                    ON session_states(scheduled_resume) 
                    WHERE scheduled_resume IS NOT NULL
                """)
                
                # Create index for session state queries
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_state 
                    ON session_states(state, last_activity)
                """)
                
                conn.commit()
                print(f"📊 Session state table initialized", file=sys.stderr)
                
        except Exception as e:
            print(f"⚠️ Failed to initialize session state table: {e}", file=sys.stderr)
    
    def _load_session_states(self):
        """Load existing session states from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT session_id, state, last_activity, scheduled_resume, 
                           retry_count, metadata
                    FROM session_states
                    WHERE last_activity > ? OR scheduled_resume > ?
                """, (time.time() - 3600, time.time()))  # Last hour or future resumes
                
                for row in cursor:
                    session_id, state, last_activity, scheduled_resume, retry_count, metadata_json = row
                    
                    metadata = {}
                    if metadata_json:
                        try:
                            metadata = json.loads(metadata_json)
                        except json.JSONDecodeError:
                            pass
                    
                    # Handle legacy states
                    try:
                        session_state = SessionState(state)
                    except ValueError:
                        # Handle legacy state names
                        if state == 'scheduled_resume':
                            session_state = SessionState.SCHEDULED_RESUME
                        else:
                            session_state = SessionState.ACTIVE  # Default fallback
                    
                    self.session_states[session_id] = SessionInfo(
                        session_id=session_id,
                        state=session_state,
                        last_activity=last_activity,
                        scheduled_resume=scheduled_resume,
                        retry_count=retry_count,
                        metadata=metadata
                    )
                
                print(f"🔄 Loaded {len(self.session_states)} session states from database", file=sys.stderr)
                
        except Exception as e:
            print(f"⚠️ Failed to load session states: {e}", file=sys.stderr)
    
    def _update_session_state(self, session_id: str, state: SessionState, 
                             scheduled_resume: Optional[float] = None,
                             increment_retry: bool = False,
                             metadata: Optional[Dict[str, Any]] = None):
        """Update session state in memory and database"""
        with self._lock:
            # Get existing session info or create new
            session_info = self.session_states.get(session_id, SessionInfo(
                session_id=session_id,
                state=state,
                last_activity=time.time()
            ))
            
            # Update fields
            session_info.state = state
            session_info.last_activity = time.time()
            
            if scheduled_resume is not None:
                session_info.scheduled_resume = scheduled_resume
            
            if increment_retry:
                session_info.retry_count += 1
            
            if metadata:
                session_info.metadata.update(metadata)
            
            # Update in memory
            self.session_states[session_id] = session_info
            
            # Persist to database
            self._persist_session_state(session_info)
    
    def _persist_session_state(self, session_info: SessionInfo):
        """Persist session state to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO session_states 
                    (session_id, state, last_activity, scheduled_resume, 
                     retry_count, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_info.session_id,
                    session_info.state.value,
                    session_info.last_activity,
                    session_info.scheduled_resume,
                    session_info.retry_count,
                    json.dumps(session_info.metadata),
                    time.time()
                ))
                conn.commit()
                
        except Exception as e:
            print(f"⚠️ Failed to persist session state for {session_info.session_id}: {e}", file=sys.stderr)
    
    async def start_continuous_operations(self):
        """Start continuous operations system with background workers"""
        if self._running:
            print("🔄 Continuous operations already running", file=sys.stderr)
            return
        
        try:
            # Store current event loop for cross-thread communication
            self._event_loop = asyncio.get_running_loop()
            
            # Start background worker thread
            self._running = True
            self._background_thread = threading.Thread(
                target=self._background_worker_loop,
                daemon=True,
                name="ContinuousOpsWorker"
            )
            self._background_thread.start()
            
            print("🚀 Continuous operations started successfully", file=sys.stderr)
            
        except Exception as e:
            print(f"⚠️ Failed to start continuous operations: {e}", file=sys.stderr)
            self._running = False
            raise
    
    def stop_continuous_operations(self):
        """Stop continuous operations gracefully"""
        print("🛑 Stopping continuous operations...", file=sys.stderr)
        
        self._running = False
        
        # Cancel all background timers
        with self._lock:
            for timer_id, timer in self.background_timers.items():
                timer.cancel()
            self.background_timers.clear()
        
        # Wait for background thread to finish
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=5.0)
        
        print("✅ Continuous operations stopped", file=sys.stderr)
    
    def _background_worker_loop(self):
        """Background worker thread for processing scheduled resumes"""
        print("🔧 Background worker started", file=sys.stderr)
        
        while self._running:
            try:
                # Check for due resumes
                due_sessions = self._get_due_sessions()
                
                for session_id in due_sessions:
                    if not self._running:
                        break
                    
                    try:
                        # Schedule async resume execution
                        if self._event_loop and not self._event_loop.is_closed():
                            future = asyncio.run_coroutine_threadsafe(
                                self._execute_auto_resume(session_id),
                                self._event_loop
                            )
                            # Don't wait for completion to avoid blocking
                            
                    except Exception as e:
                        print(f"⚠️ Error scheduling auto-resume for {session_id}: {e}", file=sys.stderr)
                
                # Sleep before next check
                time.sleep(self.TIMER_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"⚠️ Background worker error: {e}", file=sys.stderr)
                time.sleep(self.TIMER_CHECK_INTERVAL)
        
        print("🔧 Background worker stopped", file=sys.stderr)
    
    def _get_due_sessions(self) -> List[str]:
        """Get sessions that are due for auto-resume"""
        current_time = time.time()
        due_sessions = []
        
        with self._lock:
            for session_id, session_info in self.session_states.items():
                if (session_info.scheduled_resume and 
                    session_info.scheduled_resume <= current_time and
                    session_info.state == SessionState.SCHEDULED_RESUME):
                    due_sessions.append(session_id)
        
        return due_sessions
    
    async def _execute_auto_resume(self, session_id: str):
        """Execute auto-resume for a session"""
        start_time = time.time()
        
        try:
            print(f"🔄 Auto-resuming session: {session_id}", file=sys.stderr)
            
            # Update session state to active first
            self._update_session_state(
                session_id, 
                SessionState.ACTIVE,
                scheduled_resume=None,  # Clear scheduled resume
                metadata={
                    'auto_resumed_at': start_time,
                    'resume_reason': 'scheduled_auto_resume'
                }
            )
            
            # Process any queued requests for this session
            result = await self.router.process_session_queue(session_id)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            if result.get('processed_count', 0) > 0:
                print(f"✅ Auto-resume successful for {session_id}: {result['processed_count']} requests processed in {execution_time:.2f}s", file=sys.stderr)
                
                # Update metadata with success info
                self._update_session_state(
                    session_id,
                    SessionState.ACTIVE,
                    metadata={
                        'last_auto_resume_success': start_time,
                        'processed_count': result['processed_count'],
                        'execution_time_ms': int(execution_time * 1000)
                    }
                )
            else:
                print(f"ℹ️ Auto-resume completed for {session_id}: no queued requests ({execution_time:.2f}s)", file=sys.stderr)
                
                # Update metadata even for empty queue
                self._update_session_state(
                    session_id,
                    SessionState.ACTIVE,
                    metadata={
                        'last_auto_resume_check': start_time,
                        'queue_was_empty': True,
                        'execution_time_ms': int(execution_time * 1000)
                    }
                )
            
        except Exception as e:
            print(f"⚠️ Auto-resume failed for {session_id}: {e}", file=sys.stderr)
            
            # Update session state and potentially schedule retry
            session_info = self.session_states.get(session_id)
            if session_info and session_info.retry_count < self.MAX_RETRIES:
                print(f"🔄 Scheduling retry for {session_id} (attempt {session_info.retry_count + 1}/{self.MAX_RETRIES})", file=sys.stderr)
                await self._schedule_retry(session_id)
            else:
                print(f"❌ Max retries exceeded for {session_id}, marking as failed", file=sys.stderr)
                self._update_session_state(
                    session_id, 
                    SessionState.FAILED,
                    metadata={
                        'failed_at': time.time(),
                        'failure_reason': f'auto_resume_failed_after_{self.MAX_RETRIES}_retries',
                        'last_error': str(e)
                    }
                )
    
    async def schedule_auto_resume(self, session_id: str, delay_seconds: int) -> bool:
        """
        Schedule automatic resume for a session after rate limit.
        
        Args:
            session_id: Session to schedule resume for
            delay_seconds: Delay before resume in seconds
            
        Returns:
            True if scheduled successfully
        """
        try:
            # Calculate resume time
            resume_time = time.time() + delay_seconds
            
            # Update session state
            self._update_session_state(
                session_id, 
                SessionState.SCHEDULED_RESUME,
                scheduled_resume=resume_time,
                metadata={
                    'scheduled_at': time.time(),
                    'delay_seconds': delay_seconds,
                    'reason': 'rate_limit_recovery'
                }
            )
            
            print(f"⏰ Scheduled auto-resume for {session_id} in {delay_seconds}s", file=sys.stderr)
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to schedule auto-resume for {session_id}: {e}", file=sys.stderr)
            return False
    
    async def _schedule_retry(self, session_id: str):
        """Schedule retry for failed auto-resume with exponential backoff"""
        session_info = self.session_states.get(session_id)
        if not session_info:
            return
        
        # Calculate delay with exponential backoff
        delay = min(
            self.MAX_RETRY_DELAY,
            self.BASE_RETRY_DELAY * (2 ** session_info.retry_count)
        )
        
        # Schedule retry
        await self.schedule_auto_resume(session_id, delay)
        
        # Increment retry count
        self._update_session_state(session_id, SessionState.SCHEDULED_RESUME, increment_retry=True)
        
        print(f"🔄 Scheduled retry {session_info.retry_count + 1}/{self.MAX_RETRIES} for {session_id} in {delay}s", file=sys.stderr)
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session state with auto-resume information.
        
        Args:
            session_id: Session ID to get state for
            
        Returns:
            Dictionary with session state information
        """
        session_info = self.session_states.get(session_id)
        
        if not session_info:
            return {
                'session_id': session_id,
                'state': SessionState.ACTIVE.value,
                'last_activity': None,
                'scheduled_resume': None,
                'retry_count': 0,
                'metadata': {}
            }
        
        return {
            'session_id': session_info.session_id,
            'state': session_info.state.value,
            'last_activity': session_info.last_activity,
            'scheduled_resume': session_info.scheduled_resume,
            'retry_count': session_info.retry_count,
            'metadata': session_info.metadata,
            'is_due_for_resume': (
                session_info.scheduled_resume and 
                session_info.scheduled_resume <= time.time() and
                session_info.state == SessionState.SCHEDULED_RESUME
            )
        }
    
    def get_all_session_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all session states"""
        return {
            session_id: self.get_session_state(session_id)
            for session_id in self.session_states.keys()
        }
    
    # === SESSION LIFECYCLE MANAGEMENT WITH AUTO-RESTART ===
    
    def check_session_health(self, session_id: str) -> bool:
        """Check if a session is healthy and active"""
        with self._lock:
            session_info = self.session_states.get(session_id)
            if not session_info:
                return False
            
            # Check if session has been inactive for too long
            inactive_threshold = 3600  # 1 hour
            if time.time() - session_info.last_activity > inactive_threshold:
                return False
            
            # Check if session is in a failed state
            if session_info.state in [SessionState.FAILED, SessionState.ERROR]:
                return False
            
            # Check if retry count is too high
            max_retries = 5
            if session_info.retry_count >= max_retries:
                return False
            
            return True
    
    async def restart_session(self, session_id: str, reason: str = "auto_restart") -> bool:
        """Restart a failed or inactive session with exponential backoff"""
        try:
            with self._lock:
                session_info = self.session_states.get(session_id)
                if not session_info:
                    print(f"⚠️ Cannot restart non-existent session: {session_id}", file=sys.stderr)
                    return False
                
                # Calculate exponential backoff delay
                base_delay = 60  # 1 minute base delay
                delay = min(base_delay * (2 ** session_info.retry_count), 3600)  # Max 1 hour
                
                print(f"🔄 Restarting session {session_id} after {delay}s delay (attempt {session_info.retry_count + 1})", file=sys.stderr)
                
                # Update session state to RESTARTING with metadata
                restart_metadata = {
                    'restart_reason': reason,
                    'restart_at': time.time(),
                    'previous_state': session_info.state.value,
                    'retry_attempt': session_info.retry_count + 1
                }
                
                self._update_session_state(
                    session_id,
                    SessionState.RESTARTING,
                    scheduled_resume=time.time() + delay,
                    increment_retry=True,
                    metadata=restart_metadata
                )
                
                # Schedule restart execution
                await self.schedule_auto_resume(session_id, delay)
                return True
                
        except Exception as e:
            print(f"❌ Failed to restart session {session_id}: {e}", file=sys.stderr)
            return False
    
    async def perform_health_check(self):
        """Perform comprehensive health check on all active sessions"""
        try:
            print("🏥 Performing session health check...", file=sys.stderr)
            
            unhealthy_sessions = []
            total_sessions = 0
            
            with self._lock:
                for session_id, session_info in self.session_states.items():
                    total_sessions += 1
                    if not self.check_session_health(session_id):
                        unhealthy_sessions.append(session_id)
            
            print(f"📊 Health check: {total_sessions} total, {len(unhealthy_sessions)} unhealthy", file=sys.stderr)
            
            # Restart unhealthy sessions
            restart_count = 0
            for session_id in unhealthy_sessions:
                if await self.restart_session(session_id, "health_check"):
                    restart_count += 1
            
            print(f"✅ Health check complete: {restart_count} sessions restarted", file=sys.stderr)
            
        except Exception as e:
            print(f"❌ Health check failed: {e}", file=sys.stderr)
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get comprehensive session metrics for observability"""
        try:
            with self._lock:
                state_counts = {}
                total_retries = 0
                avg_activity_age = 0
                current_time = time.time()
                
                for session_info in self.session_states.values():
                    state = session_info.state.value
                    state_counts[state] = state_counts.get(state, 0) + 1
                    total_retries += session_info.retry_count
                    avg_activity_age += (current_time - session_info.last_activity)
                
                total_sessions = len(self.session_states)
                avg_activity_age = avg_activity_age / total_sessions if total_sessions > 0 else 0
                
                return {
                    'total_sessions': total_sessions,
                    'state_distribution': state_counts,
                    'total_retries': total_retries,
                    'avg_activity_age_seconds': avg_activity_age,
                    'background_timers_active': len(self.background_timers),
                    'last_health_check': current_time
                }
                
        except Exception as e:
            print(f"⚠️ Failed to get session metrics: {e}", file=sys.stderr)
            return {'error': str(e)}
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session states to prevent database bloat"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM session_states 
                    WHERE last_activity < ? AND (scheduled_resume IS NULL OR scheduled_resume < ?)
                """, (cutoff_time, time.time()))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    print(f"🧹 Cleaned up {deleted_count} old session states", file=sys.stderr)
                
                # Also clean up in-memory states
                with self._lock:
                    old_sessions = [
                        sid for sid, info in self.session_states.items()
                        if (info.last_activity < cutoff_time and 
                            (not info.scheduled_resume or info.scheduled_resume < time.time()))
                    ]
                    
                    for session_id in old_sessions:
                        del self.session_states[session_id]
                
        except Exception as e:
            print(f"⚠️ Failed to cleanup old session states: {e}", file=sys.stderr)


def create_continuous_operation_manager(smart_router: SmartAPIRouter) -> ContinuousOperationManager:
    """
    Factory function to create ContinuousOperationManager.
    
    Args:
        smart_router: SmartAPIRouter instance to wrap
        
    Returns:
        Configured ContinuousOperationManager instance
    """
    return ContinuousOperationManager(smart_router)


# Context manager for automatic lifecycle management
class ContinuousOperationContext:
    """Context manager for automatic continuous operation lifecycle"""
    
    def __init__(self, continuous_manager: ContinuousOperationManager):
        self.manager = continuous_manager
    
    async def __aenter__(self):
        await self.manager.start_continuous_operations()
        return self.manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.manager.stop_continuous_operations()


if __name__ == "__main__":
    # Basic test/demo
    import asyncio
    from utils.smart_api_router import create_smart_router
    
    async def demo():
        router = create_smart_router()
        manager = create_continuous_operation_manager(router)
        
        async with ContinuousOperationContext(manager) as ops:
            print("Demo: Continuous operations active")
            
            # Schedule a test auto-resume
            await ops.schedule_auto_resume("test_session", 10)
            
            # Get session state
            state = ops.get_session_state("test_session")
            print(f"Session state: {state}")
            
            await asyncio.sleep(2)
    
    asyncio.run(demo())