---
name: safe-gemini
description: Safe Gemini CLI wrapper command for large codebase analysis with comprehensive safeguards
---

# Safe Gemini CLI Command

## Purpose
Provides a safe, monitored way to use Gemini CLI for large codebase analysis while preventing any unwanted file modifications.

## Usage

### Basic Syntax
```bash
/safe-gemini <analysis_type> <path> [additional_context]
```

### Analysis Types

#### `architecture` - System Architecture Analysis
```bash
/safe-gemini architecture /path/to/codebase
```
Analyzes overall system architecture, design patterns, and component relationships.

#### `quality` - Code Quality Assessment  
```bash
/safe-gemini quality /path/to/codebase
```
Assesses code quality, best practices adherence, and maintainability issues.

#### `security` - Security Vulnerability Analysis
```bash
/safe-gemini security /path/to/codebase  
```
Identifies potential security vulnerabilities and risks without suggesting fixes.

#### `dependencies` - Dependency Analysis
```bash
/safe-gemini dependencies /path/to/codebase
```
Analyzes project dependencies, frameworks, and third-party integrations.

#### `custom` - Custom Analysis Query
```bash
/safe-gemini custom /path/to/codebase "Describe the testing strategy used in this codebase"
```

## Implementation

This command automatically:

1. **Creates git backup** before analysis
2. **Validates prompt safety** (ensures read-only analysis)  
3. **Monitors file changes** during execution
4. **Rolls back modifications** if any detected
5. **Provides comprehensive logging** of safety checks

## Safety Features

### Automatic Safeguards
- ✅ **Prompt Validation**: Ensures only read-only analysis prompts
- ✅ **Git Backup**: Creates commit before any Gemini CLI operation
- ✅ **File Monitoring**: Tracks all file modifications during execution  
- ✅ **Auto Rollback**: Immediately reverts any file changes
- ✅ **Safety Logging**: Comprehensive audit trail of all operations

### Forbidden Operations
The command will REJECT prompts containing:
- "fix", "implement", "create", "modify", "update", "edit"
- "write", "save", "delete", "remove", "refactor"
- "optimize", "improve", "add", "install", "configure"

### Required Safety Prefix
All analysis prompts automatically include:
```
"ANALYZE ONLY - DO NOT MODIFY: [your analysis request]"
```

## Examples

### Comprehensive Codebase Analysis
```bash
/safe-gemini architecture .
```
Output: Detailed architecture analysis with component relationships, design patterns, and system overview.

### Security Focused Analysis
```bash
/safe-gemini security ./src
```  
Output: Security vulnerability assessment with risk identification and categorization.

### Custom Analysis with Context
```bash
/safe-gemini custom . "Analyze the testing strategy and coverage approach used in this project"
```
Output: Custom analysis focusing on testing methodologies and coverage patterns.

## Integration with Subagents

### Code Reviewer Integration
When `code-reviewer` needs large codebase analysis:
```bash
/safe-gemini quality $CODEBASE_PATH
```

### Security Specialist Integration  
When `security-specialist` needs comprehensive security analysis:
```bash
/safe-gemini security $CODEBASE_PATH
```

### Backend Architect Integration
When `backend-architect` needs system architecture understanding:
```bash
/safe-gemini architecture $CODEBASE_PATH
```

## Error Handling

### If File Modifications Detected
1. **Immediate rollback** executed automatically
2. **Incident logged** with full details
3. **Analysis results discarded** for safety
4. **User notified** of safety violation

### If Unsafe Prompt Detected
1. **Operation terminated** before Gemini CLI execution
2. **User notified** of unsafe prompt elements
3. **Safe alternatives suggested** for the analysis request

### If Gemini CLI Unavailable
1. **Graceful fallback** to standard Claude analysis
2. **User notified** of limited context window
3. **Suggestion provided** to break analysis into smaller chunks

## Best Practices

### For Subagents
1. **Always use `/safe-gemini`** instead of direct `gemini` commands
2. **Specify analysis type** clearly for optimized prompts
3. **Provide context** about what aspect you're analyzing
4. **Review safety logs** if unexpected results occur

### For Complex Analysis
1. **Break large analysis** into focused areas (architecture, security, quality)
2. **Use specific paths** rather than entire repository when possible
3. **Combine results** from multiple focused analyses for comprehensive understanding

## Monitoring and Compliance

### Safety Metrics Tracked
- Number of successful analyses without modifications
- Prompt safety validation success rate  
- File modification detection accuracy
- Rollback execution success rate

### Compliance Reporting
- All Gemini CLI operations logged with timestamps
- Safety check results archived for audit
- File modification incidents tracked and analyzed
- Prompt patterns analyzed for safety improvements

## Troubleshooting

### Common Issues

**"Unsafe prompt detected"**
- Review prompt for modification keywords
- Use analysis-focused language ("describe", "analyze", "assess")
- Add specific context about read-only nature

**"Gemini CLI timeout"**  
- Try smaller scope analysis (specific directories)
- Break complex analysis into multiple focused queries
- Check Gemini CLI configuration and authentication

**"File modifications detected"**
- Automatic rollback already executed
- Review incident logs for pattern analysis
- Consider updating prompt safety patterns
- Report incident for safety pattern improvement