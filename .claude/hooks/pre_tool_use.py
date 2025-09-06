#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
import subprocess
from pathlib import Path
from utils.constants import ensure_session_log_dir

def is_dangerous_rm_command(command):
    """
    Comprehensive detection of dangerous rm commands.
    Matches various forms of rm -rf and similar destructive patterns.
    """
    # Normalize command by removing extra spaces and converting to lowercase
    normalized = ' '.join(command.lower().split())
    
    # Pattern 1: Standard rm -rf variations
    patterns = [
        r'\brm\s+.*-[a-z]*r[a-z]*f',  # rm -rf, rm -fr, rm -Rf, etc.
        r'\brm\s+.*-[a-z]*f[a-z]*r',  # rm -fr variations
        r'\brm\s+--recursive\s+--force',  # rm --recursive --force
        r'\brm\s+--force\s+--recursive',  # rm --force --recursive
        r'\brm\s+-r\s+.*-f',  # rm -r ... -f
        r'\brm\s+-f\s+.*-r',  # rm -f ... -r
    ]
    
    # Check for dangerous patterns
    for pattern in patterns:
        if re.search(pattern, normalized):
            return True
    
    # Pattern 2: Check for rm with recursive flag targeting dangerous paths
    dangerous_paths = [
        r'/',           # Root directory
        r'/\*',         # Root with wildcard
        r'~',           # Home directory
        r'~/',          # Home directory path
        r'\$HOME',      # Home environment variable
        r'\.\.',        # Parent directory references
        r'\*',          # Wildcards in general rm -rf context
        r'\.',          # Current directory
        r'\.\s*$',      # Current directory at end of command
    ]
    
    if re.search(r'\brm\s+.*-[a-z]*r', normalized):  # If rm has recursive flag
        for path in dangerous_paths:
            if re.search(path, normalized):
                return True
    
    return False

def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    """
    if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write', 'Bash']:
        # Check file paths for file-based tools
        if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write']:
            file_path = tool_input.get('file_path', '')
            if '.env' in file_path and not file_path.endswith('.env.sample'):
                return True
        
        # Check bash commands for .env file access
        elif tool_name == 'Bash':
            command = tool_input.get('command', '')
            # Pattern to detect .env file access (but allow .env.sample)
            env_patterns = [
                r'\b\.env\b(?!\.sample)',  # .env but not .env.sample
                r'cat\s+.*\.env\b(?!\.sample)',  # cat .env
                r'echo\s+.*>\s*\.env\b(?!\.sample)',  # echo > .env
                r'touch\s+.*\.env\b(?!\.sample)',  # touch .env
                r'cp\s+.*\.env\b(?!\.sample)',  # cp .env
                r'mv\s+.*\.env\b(?!\.sample)',  # mv .env
            ]
            
            for pattern in env_patterns:
                if re.search(pattern, command):
                    return True
    
    return False

def is_safe_operation(tool_name, tool_input):
    """
    Check if this is a safe operation that should be automatically authorized.
    These operations don't require manual approval for better UX.
    """
    
    # Safe tools that are always allowed (read-only + safe write operations)
    safe_tools = {
        # Read-only operations
        'Read', 'Glob', 'Grep', 'LS', 'BashOutput', 'ListMcpResourcesTool',
        'ReadMcpResourceTool', 'WebFetch', 'WebSearch', 
        
        # Safe write operations
        'TodoWrite', 'Write', 'Edit', 'MultiEdit', 'NotebookEdit',
        
        # System operations (generally safe)
        'ExitPlanMode', 'KillBash',
        
        # All Task tool operations (orchestration)
        'Task'
    }
    
    if tool_name in safe_tools:
        return True
    
    # Safe Bash commands (read-only operations)
    if tool_name == 'Bash':
        command = tool_input.get('command', '').strip()
        
        # Safe read-only commands
        safe_bash_patterns = [
            r'^ls\b',           # ls command
            r'^cat\b',          # cat command  
            r'^head\b',         # head command
            r'^tail\b',         # tail command
            r'^grep\b',         # grep command
            r'^find\b',         # find command (always allowed for file searching)
            r'^wc\b',           # word count
            r'^du\b',           # disk usage
            r'^df\b',           # disk free
            r'^ps\b',           # process list
            r'^top\b',          # system monitor
            r'^lsof\b',         # list open files
            r'^pwd\b',          # print working directory
            r'^whoami\b',       # current user
            r'^date\b',         # current date
            r'^echo\s+\$',      # echo environment variables
            r'^env\b',          # environment variables
            r'^which\b',        # which command
            r'^where\b',        # where command  
            r'^type\b',         # type command
            r'^curl\b',         # curl commands (always allowed for API testing)
            r'^curl\s+.*-s\b',  # silent curl (often read-only)
            r'curl.*',          # all curl variations
            r'^time\s+curl\b',  # time curl (performance testing)
            r'^jq\b',           # jq command (JSON processing)
            r'.*\|\s*jq\b',     # piped to jq
            r'^git\s+status\b', # git status
            r'^git\s+log\b',    # git log
            r'^git\s+diff\b',   # git diff
            r'^git\s+branch\b', # git branch
            r'^git\s+add\b',    # git add (safe for commits)
            r'^git\s+commit\b', # git commit (safe)
            r'^python3?\s+.*--version\b',  # version checks
            r'^node\s+.*--version\b',      # version checks
            r'^npm\s+.*--version\b',       # version checks  
            r'^bun\s+.*--version\b',       # version checks
            r'^docker\s+ps\b',             # docker process list
            r'^docker\s+logs\b',           # docker logs
            r'^docker\s+inspect\b',        # docker inspect
            r'^timeout\s+\d+\s+',          # timeout commands
            r'^chmod\s+\+x\s+',            # make executable
            r'^mkdir\s+',                  # create directories
            r'^touch\s+',                  # create files
            r'^cp\s+',                     # copy files
            r'^mv\s+',                     # move files (generally safe)
            r'^uv\s+run\s+',               # uv run (Python execution)
            r'^python3?\s+.*\.py\b',       # Python script execution
            r'^\./',                       # execute local scripts
            r'^\./scripts/',               # execute scripts directory
            r'^netstat\b',                 # network status
            r'^wget\b',                    # wget downloads
            r'.*\|\s*head\b',              # piped to head
            r'.*\|\s*tail\b',              # piped to tail
            r'.*\|\s*grep\b',              # piped to grep
            r'.*2>/dev/null',              # redirected stderr
            r'.*\|\s*wc\b',                # piped to word count
        ]
        
        # Check if command matches safe patterns
        for pattern in safe_bash_patterns:
            if re.match(pattern, command, re.IGNORECASE):
                return True
    
    # UNIVERSAL MCP OPERATIONS AUTO-APPROVAL
    # Most MCP servers are designed for safe operations (research, documentation, memory, etc.)
    # Auto-approve ALL MCP operations unless explicitly blocked
    if tool_name.startswith('mcp__'):
        # Define any potentially dangerous MCP operations to exclude (if any in future)
        dangerous_mcp_patterns = [
            # Add specific dangerous MCP operations here if needed
            # Currently all known MCP servers are safe for automation
        ]
        
        # Check if this MCP operation should be blocked
        is_dangerous = any(pattern in tool_name for pattern in dangerous_mcp_patterns)
        
        if not is_dangerous:
            return True  # Auto-approve all MCP operations by default
    
    return False


def call_todowrite_sync(input_data):
    """
    Call TodoWrite synchronization hook for TodoWrite tool calls
    """
    try:
        tool_name = input_data.get('tool_name', '')
        
        if tool_name == 'TodoWrite':
            # Get the current directory where the hook is located
            hook_dir = Path(__file__).parent
            todowrite_sync_path = hook_dir / 'todowrite_sync.py'
            
            if todowrite_sync_path.exists():
                # Call the TodoWrite sync hook
                result = subprocess.run(
                    ['uv', 'run', str(todowrite_sync_path)],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    timeout=10  # 10 second timeout
                )
                
                # Check if sync hook executed successfully
                if result.returncode == 0:
                    # Log successful sync
                    if result.stderr:
                        print(result.stderr, file=sys.stderr)
                else:
                    # Log sync failure but continue
                    print(f"TodoWrite sync hook failed (return code {result.returncode}): {result.stderr}", file=sys.stderr)
                    
    except subprocess.TimeoutExpired:
        print("TodoWrite sync hook timed out - continuing with original call", file=sys.stderr)
    except Exception as error:
        print(f"Error calling TodoWrite sync hook: {error}", file=sys.stderr)


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        
        # TODOWRITE SYNCHRONIZATION: Call sync hook before processing
        call_todowrite_sync(input_data)
        
        # OPTIMIZATION: Auto-approve safe operations for better UX
        if is_safe_operation(tool_name, tool_input):
            # Skip authorization for safe operations - improve Claude Code UX
            pass  # Allow the operation to proceed without blocking
        
        # Check for .env file access (blocks access to sensitive environment files)
        if is_env_file_access(tool_name, tool_input):
            print("BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude
        
        # Check for dangerous rm -rf commands
        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            
            # Block rm -rf commands with comprehensive pattern matching
            if is_dangerous_rm_command(command):
                print("BLOCKED: Dangerous rm command detected and prevented", file=sys.stderr)
                sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude
        
        # Extract session_id
        session_id = input_data.get('session_id', 'unknown')
        
        # Ensure session log directory exists
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / 'pre_tool_use.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()