#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///

"""
Agent Detection Utility for Multi-Agent Observability

Detects which Claude Code sub-agent is currently active and extracts
metadata for observability tracking.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Optional, List


# Agent Role Categories for Observability
AGENT_CATEGORIES = {
    'core_development': [
        'primary-agent', 'planner', 'coder', 'code-reviewer', 
        'tester-debugger', 'optimizer', 'system-admin', 'researcher'
    ],
    'quality_assurance': [
        'code-reviewer', 'tester-debugger', 'cleanup-validator',
        'github-copilot-reviewer'
    ],
    'security': [
        'security-specialist', 'code-reviewer'
    ],
    'design_architecture': [
        'database-architect', 'ui-ux-designer', 'optimizer'
    ],
    'domain_specialists': [
        'mathematician', 'researcher', 'security-specialist',
        'database-architect', 'ui-ux-designer'
    ]
}

# Agent Role Mapping
AGENT_ROLES = {
    'primary-agent': 'orchestrator',
    'planner': 'planning',
    'coder': 'development',
    'code-reviewer': 'quality',
    'tester-debugger': 'testing',
    'optimizer': 'performance',
    'system-admin': 'devops',
    'researcher': 'research',
    'mathematician': 'computation',
    'database-architect': 'architecture',
    'security-specialist': 'security',
    'ui-ux-designer': 'design',
    'github-copilot-reviewer': 'automation',
    'cleanup-validator': 'validation'
}


def get_current_agent_context() -> Dict[str, Optional[str]]:
    """
    Detect current Claude Code sub-agent from environment and context.
    
    Returns:
        Dict containing agent_name, agent_role, agent_category, and delegation_chain
    """
    
    # Method 1: Check environment variables (Claude Code sets these)
    agent_name = os.getenv('CLAUDE_AGENT_NAME')
    if agent_name:
        return build_agent_metadata(agent_name)
    
    # Method 2: Parse from current session/process title
    session_info = get_session_agent_info()
    if session_info.get('agent_name'):
        return build_agent_metadata(session_info['agent_name'])
    
    # Method 3: Analyze recent log files for agent patterns
    log_agent = detect_agent_from_logs()
    if log_agent:
        return build_agent_metadata(log_agent)
    
    # Default: Primary Agent (fallback)
    return build_agent_metadata('primary-agent')


def build_agent_metadata(agent_name: str) -> Dict[str, Optional[str]]:
    """Build complete metadata for an agent."""
    
    agent_role = AGENT_ROLES.get(agent_name, 'unknown')
    agent_category = get_agent_category(agent_name)
    
    # Build delegation chain (Primary → Specialist pattern)
    delegation_chain = 'primary-agent'
    if agent_name != 'primary-agent':
        delegation_chain = f'primary-agent → {agent_name}'
    
    return {
        'agent_name': agent_name,
        'agent_role': agent_role,
        'agent_category': agent_category,
        'delegation_chain': delegation_chain,
        'timestamp': int(os.time.time() * 1000) if hasattr(os, 'time') else None
    }


def get_agent_category(agent_name: str) -> str:
    """Determine agent category for UI grouping."""
    for category, agents in AGENT_CATEGORIES.items():
        if agent_name in agents:
            return category
    return 'other'


def get_session_agent_info() -> Dict[str, Optional[str]]:
    """Extract agent info from current session context."""
    
    # Check if we're in a Claude Code sub-agent session
    try:
        # Parse process information for agent indicators
        import psutil
        current_process = psutil.Process()
        
        # Check command line arguments for agent indicators
        cmdline = ' '.join(current_process.cmdline())
        
        # Look for agent patterns in command line
        agent_patterns = [
            r'--agent[=\s]+([a-z-]+)',
            r'claude[_\s]+agent[_\s]+([a-z-]+)',
            r'subagent[_\s]+([a-z-]+)'
        ]
        
        for pattern in agent_patterns:
            match = re.search(pattern, cmdline, re.IGNORECASE)
            if match:
                return {'agent_name': match.group(1)}
                
    except ImportError:
        pass
    
    return {}


def detect_agent_from_logs() -> Optional[str]:
    """Detect agent from recent log entries."""
    
    try:
        log_dir = Path.cwd() / 'logs'
        if not log_dir.exists():
            return None
        
        # Check recent subagent_stop.json for last active agent
        subagent_log = log_dir / 'subagent_stop.json'
        if subagent_log.exists():
            with open(subagent_log, 'r') as f:
                import json
                log_data = json.load(f)
                
                if log_data and isinstance(log_data, list) and len(log_data) > 0:
                    latest_entry = log_data[-1]
                    
                    # Extract agent name from session_id or payload
                    session_id = latest_entry.get('session_id', '')
                    if any(agent in session_id.lower() for agent in AGENT_ROLES.keys()):
                        for agent in AGENT_ROLES.keys():
                            if agent in session_id.lower():
                                return agent
    
    except Exception:
        pass
    
    return None


def get_agent_list() -> List[Dict[str, str]]:
    """Get list of all configured Claude Code agents."""
    
    agents_dir = Path.cwd() / '.claude' / 'agents'
    if not agents_dir.exists():
        return []
    
    agents = []
    for agent_file in agents_dir.glob('*.md'):
        agent_name = agent_file.stem
        if agent_name in AGENT_ROLES:
            agents.append({
                'name': agent_name,
                'role': AGENT_ROLES[agent_name],
                'category': get_agent_category(agent_name),
                'file_path': str(agent_file)
            })
    
    return sorted(agents, key=lambda x: x['name'])


def validate_agent_config(agent_name: str) -> bool:
    """Validate that an agent configuration exists and is properly formatted."""
    
    agents_dir = Path.cwd() / '.claude' / 'agents'
    agent_file = agents_dir / f'{agent_name}.md'
    
    if not agent_file.exists():
        return False
    
    try:
        with open(agent_file, 'r') as f:
            content = f.read()
            
        # Check for YAML frontmatter
        if not content.startswith('---'):
            return False
        
        # Extract YAML frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return False
        
        yaml_content = parts[1]
        metadata = yaml.safe_load(yaml_content)
        
        # Validate required fields
        required_fields = ['name', 'description']
        return all(field in metadata for field in required_fields)
        
    except Exception:
        return False


if __name__ == '__main__':
    import json
    
    # Output current agent metadata as JSON
    metadata = get_current_agent_context()
    print(json.dumps(metadata, indent=2))