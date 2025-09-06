---
name: safe-litellm-analysis
description: Safe wrapper for using Smart API Router through liteLLM proxy for read-only codebase analysis
---

# Safe Smart API Router Analysis Command

## Purpose
Provides safe patterns for using the Smart API Router through liteLLM proxy to analyze codebases with intelligent Claude/Gemini routing while preventing unwanted modifications.

## Smart API Router Integration

### **Intelligent Provider Selection**
- **Primary Route**: Anthropic Claude (direct API) for standard analysis
- **Fallback Route**: Gemini via liteLLM proxy when Claude is rate limited
- **Queue Management**: Session-based request queuing during rate limit periods
- **Real-time Monitoring**: Provider health checks and automatic switching

## Safety Principles

### **READ-ONLY ANALYSIS ONLY**
- Never use Smart API Router for code generation or modification
- Only use for analysis, review, and understanding
- Always use explicit "analyze" and "describe" language
- Never request "implement", "create", "modify", "fix"

### **Safe Prompt Patterns**

#### ✅ SAFE Prompts (Read-Only Analysis):
```bash
# Architecture analysis through Smart API Router
python3 .claude/scripts/safe-litellm-wrapper.py . "ANALYZE ONLY - DO NOT MODIFY: Analyze and describe the architecture of this system. What are the main components and how do they interact?"

# Code quality assessment through intelligent routing
python3 .claude/scripts/safe-litellm-wrapper.py ./src "ANALYZE ONLY - DO NOT MODIFY: Analyze the code quality of this codebase. Identify patterns, potential issues, and adherence to best practices."

# Security analysis with fallback capabilities
python3 .claude/scripts/safe-litellm-wrapper.py . "ANALYZE ONLY - DO NOT MODIFY: Analyze this codebase for potential security vulnerabilities. Describe any risks found without suggesting fixes."

# Dependency analysis with provider optimization
python3 .claude/scripts/safe-litellm-wrapper.py . "ANALYZE ONLY - DO NOT MODIFY: Analyze the dependencies and integration patterns used in this project. What libraries and frameworks are being used?"
```

#### ❌ DANGEROUS Prompts (Avoid These):
```bash
# These can modify files - NEVER USE:
python3 .claude/scripts/safe-litellm-wrapper.py . "Fix the bugs in this code"
python3 .claude/scripts/safe-litellm-wrapper.py . "Implement feature X"  
python3 .claude/scripts/safe-litellm-wrapper.py . "Create a new component"
python3 .claude/scripts/safe-litellm-wrapper.py . "Update the configuration"
```

## Safe Usage Workflow

### **Step 1: Smart Router Safety Check**
```bash
# Always verify Smart API Router is running
curl -f http://localhost:4001/v1/models || echo "liteLLM proxy not running"

# Check provider health
python3 -c "
import sys
sys.path.append('.claude/hooks/utils')
from smart_api_router import create_smart_router
import asyncio

async def check_status():
    router = create_smart_router()
    status = router.get_routing_status()
    print(f'Primary: {status.get(\"primary_provider\")}')
    print(f'Fallback: {status.get(\"fallback_provider\")}')
    print(f'Rate Limits: {len(status.get(\"current_rate_limits\", {}))}')

asyncio.run(check_status())
"
```

### **Step 2: Backup Safety**
```bash
# Always create backup before any analysis (handled automatically by wrapper)
git status
git add -A
git commit -m "Pre-Smart Router analysis backup"
```

### **Step 3: Read-Only Analysis Commands**

#### **Comprehensive Codebase Analysis:**
```bash
python3 .claude/scripts/safe-litellm-wrapper.py . "
ANALYZE ONLY - DO NOT MODIFY:
Provide a comprehensive analysis of this codebase including:
1. Overall architecture and design patterns
2. Code quality assessment and adherence to best practices  
3. Security considerations and potential vulnerabilities
4. Performance implications and bottlenecks
5. Maintainability and technical debt assessment
6. Integration points and dependencies
7. Smart API Router compatibility and usage patterns

Format as structured analysis report with JSON output.
"
```

#### **Specific Component Analysis:**
```bash
# Smart API Router system analysis
python3 .claude/scripts/safe-litellm-wrapper.py .claude/hooks/utils "
ANALYZE ONLY - DO NOT MODIFY: Describe the Smart API Router implementation. How does it handle Claude/Gemini routing and fallback logic?"

# Agent system analysis  
python3 .claude/scripts/safe-litellm-wrapper.py .claude/agents "
ANALYZE ONLY - DO NOT MODIFY: Analyze the agent configuration system. How are agents configured for AI model routing?"

# Configuration analysis
python3 .claude/scripts/safe-litellm-wrapper.py . "
ANALYZE ONLY - DO NOT MODIFY: Analyze the liteLLM and Smart API Router configuration. How is Claude/Gemini routing implemented?"
```

### **Step 4: Post-Analysis Verification**
```bash
# Verify no files were modified (handled automatically by wrapper)
git status
git diff

# Check Smart API Router metrics
python3 -c "
import sys
sys.path.append('.claude/hooks/utils')
from smart_api_router import create_smart_router
import asyncio

async def show_metrics():
    router = create_smart_router()
    status = router.get_routing_status()
    print('Routing Statistics:', status.get('routing_stats', {}))
    print('Recommendations:', status.get('recommendations', []))

asyncio.run(show_metrics())
"
```

## Smart Router Implementation for Subagents

### **Code-Reviewer Safe Pattern:**
```python
def safe_smart_router_analysis(self, codebase_path, analysis_type):
    """
    Safe wrapper for Smart API Router codebase analysis
    """
    import subprocess
    import json
    
    # Pre-analysis safety check
    subprocess.run(["git", "status", "--porcelain"], check=True)
    
    # Construct safe read-only prompt
    safe_prompts = {
        "architecture": f"ANALYZE ONLY - DO NOT MODIFY: Describe the architecture and main components of this system using Smart API Router.",
        "quality": f"ANALYZE ONLY - DO NOT MODIFY: Assess code quality, patterns, and adherence to best practices via intelligent routing.",
        "security": f"ANALYZE ONLY - DO NOT MODIFY: Identify potential security vulnerabilities and risks through Smart API Router analysis."
    }
    
    prompt = safe_prompts.get(analysis_type, safe_prompts["quality"])
    
    # Execute analysis through Smart API Router
    result = subprocess.run(
        ["python3", ".claude/scripts/safe-litellm-wrapper.py", codebase_path, prompt],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    # Parse result
    if result.returncode == 0:
        try:
            # Extract JSON from output
            output_lines = result.stdout.strip().split('\n')
            json_line = None
            for line in output_lines:
                if line.startswith('JSON OUTPUT:'):
                    json_line = line.replace('JSON OUTPUT:', '').strip()
                    break
            
            if json_line:
                parsed_result = json.loads(json_line)
                if parsed_result.get("success"):
                    return parsed_result["output"]
                else:
                    raise Exception(f"Smart Router analysis failed: {parsed_result.get('error')}")
            else:
                return result.stdout
        except json.JSONDecodeError:
            return result.stdout
    else:
        raise Exception(f"Smart Router wrapper failed: {result.stderr}")
```

### **Integration in Agent Instructions:**

Update agent instructions to use Smart API Router patterns:

```markdown
### **Safe Smart API Router Usage**
When using Smart API Router for large codebase analysis:

1. **Always use READ-ONLY prompts** with explicit "ANALYZE ONLY - DO NOT MODIFY" prefix
2. **Leverage intelligent routing** between Claude and Gemini based on availability
3. **Monitor routing decisions** for optimal provider selection
4. **Use structured analysis requests** rather than open-ended prompts
5. **Verify safety checks** pass before processing results

#### **Template for Safe Analysis:**
```bash
python3 .claude/scripts/safe-litellm-wrapper.py "<path>" "ANALYZE ONLY - DO NOT MODIFY: [specific analysis request]"
```
```

## Smart Router Monitoring and Alerts

### **Provider Health Monitoring:**
```bash
#!/bin/bash
# Monitor Smart API Router health
python3 -c "
import sys
sys.path.append('.claude/hooks/utils')
from smart_api_router import create_smart_router
import asyncio
import json

async def monitor_health():
    router = create_smart_router()
    status = router.get_routing_status()
    
    print('=== Smart API Router Status ===')
    print(f'Primary Provider: {status.get(\"primary_provider\")}')
    print(f'Fallback Provider: {status.get(\"fallback_provider\")}')
    print(f'Active Rate Limits: {len(status.get(\"current_rate_limits\", {}))}')
    print(f'Should Queue: {status.get(\"should_queue\")}')
    
    recommendations = status.get('recommendations', [])
    if recommendations:
        print('\nRecommendations:')
        for rec in recommendations:
            print(f'  - {rec}')
    
    routing_stats = status.get('routing_stats', {})
    if 'totals' in routing_stats:
        totals = routing_stats['totals']
        print(f'\nTotals (24h):')
        print(f'  Requests: {totals.get(\"requests\", 0)}')
        print(f'  Success Rate: {totals.get(\"success_rate\", 0):.1%}')
        print(f'  Avg Response Time: {totals.get(\"avg_response_time_ms\", 0)}ms')

asyncio.run(monitor_health())
"
```

## Emergency Procedures

### **If Smart Router Analysis Fails:**
1. **Check Provider Status:** Verify both Claude and Gemini availability
2. **Review Queue Status:** Check if requests are being queued
3. **Fallback to Manual:** Use direct Claude Code analysis if both providers fail
4. **Monitor Logs:** Check Smart API Router logs for routing decisions

### **If File Modifications Detected:**
1. **Automatic rollback:** Script handles git rollback automatically
2. **Review changes:** Check git status before rollback
3. **Update safety patterns:** Improve prompts to prevent future issues
4. **Report incident:** Document analysis that caused modification

## Best Practices Summary

1. **Always prefix with "ANALYZE ONLY - DO NOT MODIFY"**
2. **Use Smart API Router for intelligent Claude/Gemini routing**
3. **Monitor provider health and routing decisions**
4. **Leverage automatic fallback capabilities**
5. **Verify safety checks pass before processing results**
6. **Git backup handled automatically by wrapper**
7. **Timeout limits on analysis execution**
8. **Structured analysis requests with JSON output**

## Smart Router Configuration

### **Provider Endpoints:**
- **Claude Direct:** https://api.anthropic.com/v1/messages
- **Gemini via liteLLM:** http://localhost:4001/v1/chat/completions
- **Fallback Queue:** Session-based request management
- **Health Monitoring:** Real-time provider availability

### **Routing Logic:**
- **Primary Strategy:** Use Claude for standard analysis
- **Fallback Strategy:** Switch to Gemini when Claude rate limited
- **Queue Strategy:** Hold requests when both providers unavailable
- **Recovery Strategy:** Auto-resume when providers become available