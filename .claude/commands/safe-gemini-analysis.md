---
name: safe-gemini-analysis
description: Safe wrapper for using Gemini CLI for read-only codebase analysis without modification risks
---

# Safe Gemini CLI Analysis Command

## Purpose
Provides safe patterns for using Gemini CLI to analyze codebases with large context window while preventing unwanted modifications.

## Safety Principles

### **READ-ONLY ANALYSIS ONLY**
- Never use Gemini CLI for code generation or modification
- Only use for analysis, review, and understanding
- Always use explicit "analyze" and "describe" language
- Never request "implement", "create", "modify", "fix"

### **Safe Prompt Patterns**

#### ✅ SAFE Prompts (Read-Only Analysis):
```bash
# Architecture analysis
gemini -p "@codebase/** Analyze and describe the architecture of this system. What are the main components and how do they interact?"

# Code quality assessment  
gemini -p "@src/** Analyze the code quality of this codebase. Identify patterns, potential issues, and adherence to best practices."

# Security analysis
gemini -p "@./** Analyze this codebase for potential security vulnerabilities. Describe any risks found without suggesting fixes."

# Dependency analysis
gemini -p "@package.json @requirements.txt @Cargo.toml Analyze the dependencies used in this project. What libraries and frameworks are being used?"

# Documentation analysis
gemini -p "@README.md @docs/** Analyze the documentation quality and coverage for this project."
```

#### ❌ DANGEROUS Prompts (Avoid These):
```bash
# These can modify files - NEVER USE:
gemini -p "Fix the bugs in this code"
gemini -p "Implement feature X"  
gemini -p "Create a new component"
gemini -p "Update the configuration"
gemini -p "Optimize this function"
```

## Safe Usage Workflow

### **Step 1: Backup Safety**
```bash
# Always create backup before any Gemini CLI usage
git status
git add -A
git commit -m "Pre-Gemini analysis backup"
```

### **Step 2: Read-Only Analysis Commands**

#### **Comprehensive Codebase Analysis:**
```bash
gemini -p "@./** 
ANALYZE ONLY - DO NOT MODIFY:
Provide a comprehensive analysis of this codebase including:
1. Overall architecture and design patterns
2. Code quality assessment and adherence to best practices  
3. Security considerations and potential vulnerabilities
4. Performance implications and bottlenecks
5. Maintainability and technical debt assessment
6. Integration points and dependencies
7. Documentation quality and coverage

Format as structured analysis report."
```

#### **Specific Component Analysis:**
```bash
# Hooks system analysis
gemini -p "@.claude/hooks/** 
ANALYZE ONLY: Describe the purpose and implementation of this hooks system. What events are handled and how?"

# Agent system analysis  
gemini -p "@.claude/agents/**
ANALYZE ONLY: Analyze the agent configuration system. What types of agents are defined and what are their capabilities?"

# Configuration analysis
gemini -p "@.claude/settings.json @CLAUDE.md
ANALYZE ONLY: Analyze the configuration setup. What MCP servers and tools are configured?"
```

### **Step 3: Post-Analysis Verification**
```bash
# Verify no files were modified
git status
git diff

# If any modifications detected - immediate rollback
git checkout -- .
git clean -fd
```

## Safe Implementation for Subagents

### **Code-Reviewer Safe Pattern:**
```python
def safe_gemini_analysis(self, codebase_path, analysis_type):
    """
    Safe wrapper for Gemini CLI codebase analysis
    """
    # Pre-analysis safety check
    subprocess.run(["git", "status", "--porcelain"], check=True)
    
    # Construct safe read-only prompt
    safe_prompts = {
        "architecture": f"@{codebase_path}/** ANALYZE ONLY - DO NOT MODIFY: Describe the architecture and main components of this system.",
        "quality": f"@{codebase_path}/** ANALYZE ONLY - DO NOT MODIFY: Assess code quality, patterns, and adherence to best practices.",
        "security": f"@{codebase_path}/** ANALYZE ONLY - DO NOT MODIFY: Identify potential security vulnerabilities and risks."
    }
    
    prompt = safe_prompts.get(analysis_type, safe_prompts["quality"])
    
    # Execute analysis
    result = subprocess.run(
        ["gemini", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    # Post-analysis safety check
    git_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if git_status.stdout.strip():
        # Files were modified - rollback immediately
        subprocess.run(["git", "checkout", "--", "."])
        subprocess.run(["git", "clean", "-fd"])
        raise Exception("Gemini CLI modified files - rolled back changes")
    
    return result.stdout
```

### **Integration in Agent Instructions:**

Update agent instructions to use safe patterns:

```markdown
### **Safe Gemini CLI Usage**
When using Gemini CLI for large codebase analysis:

1. **Always use READ-ONLY prompts** with explicit "ANALYZE ONLY - DO NOT MODIFY" prefix
2. **Create git backup** before Gemini CLI execution  
3. **Verify no modifications** occurred after analysis
4. **Immediate rollback** if any files were changed
5. **Use structured analysis requests** rather than open-ended prompts

#### **Template for Safe Analysis:**
```bash
gemini -p "@codebase/** ANALYZE ONLY - DO NOT MODIFY: [specific analysis request]"
```
```

## Monitoring and Alerts

### **File Modification Detection:**
```bash
#!/bin/bash
# Pre-Gemini snapshot
find . -type f -exec stat -c "%Y %n" {} \; > /tmp/pre_gemini_snapshot

# Run Gemini analysis here

# Post-Gemini verification  
find . -type f -exec stat -c "%Y %n" {} \; > /tmp/post_gemini_snapshot
if ! diff /tmp/pre_gemini_snapshot /tmp/post_gemini_snapshot > /dev/null; then
    echo "WARNING: Files were modified by Gemini CLI!"
    git checkout -- .
    git clean -fd
    exit 1
fi
```

## Emergency Procedures

### **If Gemini CLI Modifies Files:**
1. **Immediate rollback:** `git checkout -- . && git clean -fd`
2. **Review changes:** `git status` and `git diff` before rollback
3. **Document incident:** What prompt caused the modification
4. **Update safety patterns:** Improve prompts to prevent future issues

### **Quarantine Mode:**
If repeated safety violations:
1. Disable Gemini CLI usage temporarily
2. Review all prompts and patterns
3. Implement additional safeguards
4. Test in isolated environment before re-enabling

## Best Practices Summary

1. **Always prefix with "ANALYZE ONLY - DO NOT MODIFY"**
2. **Use descriptive, analytical language** ("describe", "analyze", "assess")
3. **Avoid action words** ("fix", "implement", "create", "modify")  
4. **Git backup before every use**
5. **Verify no changes after analysis**
6. **Immediate rollback if modifications detected**
7. **Timeout limits** on Gemini CLI execution
8. **Structured analysis requests** rather than open-ended prompts