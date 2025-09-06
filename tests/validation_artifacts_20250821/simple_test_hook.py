#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "httpx",
# ]
# ///

"""
Simple Test Hook for Validation
==============================

This is a minimal hook for testing the wrapper performance without
the complexity of the full post_tool_use.py hook system.

It simulates the basic behavior:
- Reads JSON from stdin
- Processes it minimally
- Outputs JSON to stdout
- Exits with appropriate code
"""

import json
import sys
import time
import os
from typing import Dict, Any

def main():
    """Simple test hook main function"""
    start_time = time.time()
    
    try:
        # Read input from stdin if available
        if not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()
            if input_data:
                try:
                    data = json.loads(input_data)
                except json.JSONDecodeError:
                    data = {"raw_input": input_data}
            else:
                data = {"no_input": True}
        else:
            data = {"stdin_tty": True}
        
        # Add processing metadata
        result = {
            "hook_name": "simple_test_hook",
            "input_data": data,
            "processing_time_ms": (time.time() - start_time) * 1000,
            "timestamp": time.time(),
            "pid": os.getpid(),
            "success": True
        }
        
        # Output result as JSON
        print(json.dumps(result))
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        # Error handling
        error_result = {
            "hook_name": "simple_test_hook",
            "error": str(e),
            "processing_time_ms": (time.time() - start_time) * 1000,
            "timestamp": time.time(),
            "success": False
        }
        
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()