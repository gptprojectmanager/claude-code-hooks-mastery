#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

"""
Rate Limit Message Parser
========================

Parses Claude Code error messages to extract rate limit information and reset timing.
This system captures the timing data that Claude Code directly provides rather than
building complex historical analysis.

Features:
- Parses rate limit error messages from Claude Code
- Extracts reset timing information
- Stores timing data in SQLite for smart fallback routing
- Provides unified interface for rate limit detection
"""

import re
import json
import time
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from utils.constants import ensure_session_log_dir

class RateLimitParser:
    """
    Parses Claude Code rate limit messages and manages timing data.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the rate limit parser with SQLite storage."""
        if db_path is None:
            # Default to hooks directory
            hooks_dir = Path(__file__).parent.parent
            db_path = hooks_dir / "rate_limits.db"
        
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for rate limit tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider TEXT NOT NULL,
                        api_type TEXT NOT NULL,
                        error_message TEXT,
                        reset_time_seconds INTEGER,
                        reset_timestamp INTEGER,
                        extracted_at INTEGER,
                        source TEXT DEFAULT 'claude_code_message',
                        raw_data TEXT
                    )
                """)
                
                # Create index for efficient lookups
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_provider_api_reset 
                    ON rate_limits(provider, api_type, reset_timestamp)
                """)
                
                conn.commit()
                print(f"📊 Rate limit database initialized: {self.db_path}", file=sys.stderr)
                
        except Exception as e:
            print(f"⚠️ Failed to initialize rate limit database: {e}", file=sys.stderr)
    
    def parse_error_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse Claude Code error message to extract rate limit information.
        
        Args:
            message: Error message from Claude Code
            
        Returns:
            Dict with parsed rate limit info or None if not a rate limit error
        """
        
        # Claude Code rate limit message patterns
        patterns = [
            # "Rate limit exceeded. Reset in 45 seconds"
            r'rate\s+limit\s+exceeded.*?reset\s+in\s+(\d+)\s+seconds?',
            
            # "Rate limited. Try again in 2 minutes"  
            r'rate\s+limited.*?try\s+again\s+in\s+(\d+)\s+minutes?',
            
            # "API rate limit reached. Resets at 14:30"
            r'api\s+rate\s+limit.*?resets?\s+at\s+(\d{1,2}:\d{2})',
            
            # "Too many requests. Wait 30 seconds"
            r'too\s+many\s+requests.*?wait\s+(\d+)\s+seconds?',
            
            # "Request rate exceeded. Next available in 1 hour"
            r'request\s+rate\s+exceeded.*?next\s+available\s+in\s+(\d+)\s+hours?',
            
            # "Calcolo tempo di reset basato su esperienza storica: 90 secondi" - mentioned by user
            r'calcolo\s+tempo\s+di\s+reset.*?(\d+)\s+(second|minute|hour|minuti|ore|secondi)',
        ]
        
        message_lower = message.lower()
        
        # Check if this is a rate limit message
        if not any(keyword in message_lower for keyword in [
            'rate limit', 'rate limited', 'too many requests', 
            'request rate', 'api limit', 'quota exceeded',
            'calcolo tempo di reset', 'esperienza storica'
        ]):
            return None
        
        # Try to extract timing information
        for pattern in patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                try:
                    # Extract timing value
                    time_value = int(match.group(1))
                    
                    # Determine time unit from pattern or matched text
                    matched_text = match.group(0).lower() if match.group(0) else ""
                    unit_text = match.group(2).lower() if len(match.groups()) > 1 else ""
                    
                    # Check unit_text first for explicit unit detection
                    if 'minute' in unit_text or 'minuti' in unit_text:
                        reset_seconds = time_value * 60
                    elif 'hour' in unit_text or 'ore' in unit_text:
                        reset_seconds = time_value * 3600
                    elif 'second' in unit_text or 'secondi' in unit_text:
                        reset_seconds = time_value
                    # Fallback to pattern-based detection
                    elif 'minute' in pattern:
                        reset_seconds = time_value * 60
                    elif 'hour' in pattern:
                        reset_seconds = time_value * 3600
                    elif ':' in match.group(1):  # Time format like "14:30"
                        # Parse HH:MM format
                        hour, minute = map(int, match.group(1).split(':'))
                        now = datetime.now()
                        reset_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if reset_time <= now:
                            reset_time += timedelta(days=1)  # Next day
                        reset_seconds = int((reset_time - now).total_seconds())
                    else:
                        reset_seconds = time_value  # Assume seconds
                    
                    # Calculate reset timestamp
                    reset_timestamp = int(time.time()) + reset_seconds
                    
                    # Infer provider from message context
                    provider = self._infer_provider(message)
                    api_type = self._infer_api_type(message, provider)
                    
                    return {
                        'provider': provider,
                        'api_type': api_type,
                        'reset_seconds': reset_seconds,
                        'reset_timestamp': reset_timestamp,
                        'extracted_at': int(time.time()),
                        'error_message': message[:500],  # Truncate long messages
                        'source': 'claude_code_message'
                    }
                    
                except (ValueError, IndexError) as e:
                    print(f"⚠️ Error parsing timing from rate limit message: {e}", file=sys.stderr)
                    continue
        
        # If we get here, it's a rate limit message but we couldn't extract timing
        provider = self._infer_provider(message)
        api_type = self._infer_api_type(message, provider)
        
        return {
            'provider': provider,
            'api_type': api_type,
            'reset_seconds': None,
            'reset_timestamp': None,
            'extracted_at': int(time.time()),
            'error_message': message[:500],
            'source': 'claude_code_message_no_timing'
        }
    
    def _infer_provider(self, message: str) -> str:
        """Infer API provider from error message context."""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['anthropic', 'claude']):
            return 'anthropic'
        elif any(keyword in message_lower for keyword in ['google', 'gemini', 'vertex']):
            return 'google'
        elif any(keyword in message_lower for keyword in ['openai', 'gpt']):
            return 'openai'
        elif any(keyword in message_lower for keyword in ['litellm', 'proxy']):
            return 'litellm_proxy'
        else:
            return 'unknown'
    
    def _infer_api_type(self, message: str, provider: str) -> str:
        """Infer specific API type from message and provider."""
        message_lower = message.lower()
        
        if provider == 'anthropic':
            return 'direct_anthropic'
        elif provider == 'google':
            if 'vertex' in message_lower:
                return 'vertex_ai'
            else:
                return 'direct_gemini'
        elif provider == 'litellm_proxy':
            return 'proxy_mixed'
        else:
            return f'{provider}_api'
    
    def store_rate_limit(self, rate_limit_data: Dict[str, Any]) -> bool:
        """
        Store rate limit information in SQLite database.
        
        Args:
            rate_limit_data: Parsed rate limit information
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO rate_limits 
                    (provider, api_type, error_message, reset_time_seconds, 
                     reset_timestamp, extracted_at, source, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rate_limit_data['provider'],
                    rate_limit_data['api_type'],
                    rate_limit_data['error_message'],
                    rate_limit_data.get('reset_seconds'),
                    rate_limit_data.get('reset_timestamp'),
                    rate_limit_data['extracted_at'],
                    rate_limit_data['source'],
                    json.dumps(rate_limit_data)
                ))
                conn.commit()
                
                print(f"✅ Stored rate limit: {rate_limit_data['provider']} - reset in {rate_limit_data.get('reset_seconds', 'unknown')}s", file=sys.stderr)
                return True
                
        except Exception as e:
            print(f"⚠️ Failed to store rate limit data: {e}", file=sys.stderr)
            return False
    
    def get_current_rate_limits(self) -> Dict[str, Any]:
        """
        Get current active rate limits for all providers.
        
        Returns:
            Dict with current rate limit status by provider/api_type
        """
        current_time = int(time.time())
        rate_limits = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get active rate limits (where reset_timestamp > current_time)
                cursor = conn.execute("""
                    SELECT provider, api_type, reset_timestamp, reset_time_seconds, 
                           extracted_at, error_message
                    FROM rate_limits 
                    WHERE reset_timestamp > ? AND reset_timestamp IS NOT NULL
                    ORDER BY extracted_at DESC
                """, (current_time,))
                
                for row in cursor:
                    provider, api_type, reset_timestamp, reset_seconds, extracted_at, error_msg = row
                    
                    key = f"{provider}:{api_type}"
                    remaining_seconds = reset_timestamp - current_time
                    
                    rate_limits[key] = {
                        'provider': provider,
                        'api_type': api_type,
                        'is_rate_limited': True,
                        'reset_timestamp': reset_timestamp,
                        'remaining_seconds': remaining_seconds,
                        'extracted_at': extracted_at,
                        'error_message': error_msg
                    }
                
                return rate_limits
                
        except Exception as e:
            print(f"⚠️ Failed to get current rate limits: {e}", file=sys.stderr)
            return {}
    
    def should_use_fallback(self, primary_provider: str, primary_api_type: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if fallback should be used based on current rate limits.
        
        Args:
            primary_provider: Primary API provider (e.g., 'anthropic')
            primary_api_type: Primary API type (e.g., 'direct_anthropic')
            
        Returns:
            Tuple of (should_fallback, recommended_fallback_provider)
        """
        rate_limits = self.get_current_rate_limits()
        primary_key = f"{primary_provider}:{primary_api_type}"
        
        # Check if primary is rate limited
        if primary_key in rate_limits:
            remaining = rate_limits[primary_key]['remaining_seconds']
            print(f"🚫 {primary_provider} rate limited for {remaining}s", file=sys.stderr)
            
            # Recommend fallback based on primary provider
            if primary_provider == 'anthropic':
                return True, 'litellm_proxy'
            elif primary_provider == 'google':
                return True, 'anthropic'
            else:
                return True, 'anthropic'  # Default fallback
        
        return False, None
    
    def cleanup_old_records(self, max_age_hours: int = 24):
        """Clean up old rate limit records to prevent database bloat."""
        cutoff_time = int(time.time()) - (max_age_hours * 3600)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM rate_limits WHERE extracted_at < ?", (cutoff_time,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    print(f"🧹 Cleaned up {deleted_count} old rate limit records", file=sys.stderr)
                    
        except Exception as e:
            print(f"⚠️ Failed to cleanup old rate limit records: {e}", file=sys.stderr)


def parse_and_store_rate_limit(message: str, session_id: str = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to parse and store rate limit from a message.
    
    Args:
        message: Error message to parse
        session_id: Optional session ID for logging
        
    Returns:
        Parsed rate limit data or None
    """
    parser = RateLimitParser()
    
    # Parse the message
    rate_limit_data = parser.parse_error_message(message)
    
    if rate_limit_data:
        # Store in database
        parser.store_rate_limit(rate_limit_data)
        
        # Log to session if session_id provided
        if session_id:
            try:
                log_dir = ensure_session_log_dir(session_id)
                log_file = log_dir / 'rate_limits.json'
                
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        log_data = json.load(f)
                else:
                    log_data = []
                
                log_data.append(rate_limit_data)
                
                with open(log_file, 'w') as f:
                    json.dump(log_data, f, indent=2)
                    
            except Exception as e:
                print(f"⚠️ Failed to log rate limit to session: {e}", file=sys.stderr)
    
    return rate_limit_data


if __name__ == "__main__":
    # Test the rate limit parser
    test_messages = [
        "Rate limit exceeded. Reset in 45 seconds",
        "API rate limit reached. Try again in 2 minutes",
        "Too many requests. Wait 30 seconds before retrying",
        "Anthropic API rate limited. Next available at 14:30",
        "Calcolo tempo di reset basato su esperienza storica: 90 secondi",
        "Request rate exceeded for Gemini API. Wait 1 hour"
    ]
    
    parser = RateLimitParser()
    
    print("🧪 Testing Rate Limit Parser")
    for i, message in enumerate(test_messages, 1):
        print(f"\nTest {i}: {message}")
        result = parser.parse_error_message(message)
        if result:
            print(f"✅ Parsed: {result['provider']} - {result.get('reset_seconds', 'unknown')}s")
            parser.store_rate_limit(result)
        else:
            print("❌ Not recognized as rate limit message")
    
    # Test fallback logic
    print(f"\n📊 Current rate limits: {parser.get_current_rate_limits()}")
    should_fallback, recommended = parser.should_use_fallback('anthropic', 'direct_anthropic')
    print(f"🔄 Should use fallback: {should_fallback}, Recommended: {recommended}")