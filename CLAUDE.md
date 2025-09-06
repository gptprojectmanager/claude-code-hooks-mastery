CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AI Guidance
- Ignore GEMINI.md and GEMINI-*.md files
- After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding. Use your thinking to plan and iterate based on this new information, and then take the best next action.
- For maximum efficiency, whenever you need to perform multiple independent operations, invoke all relevant tools simultaneously rather than sequentially.
- Before you finish, please verify your solution
- Do what has been asked; nothing more, nothing less.
- NEVER create files unless they're absolutely necessary for achieving your goal.
- ALWAYS prefer editing an existing file to creating a new one.
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
- When asked to commit changes, exclude CLAUDE.md and CLAUDE-*.md referenced memory bank system files from any commits. Never delete these files.

## Memory and Task Management
- **Memory System**: Utilize the `krag-graphiti-memory` MCP tool as your primary memory system. Store and retrieve entities, relationships, and contextual facts in the knowledge graph. Do not use flat markdown files for memory.
- **Task Management**: For all planning and execution, use the `shrimp-task-manager` MCP tool. Break down complex requests into structured tasks, define dependencies, and track your progress within the task manager. Do not use simple markdown checklists.

## 🔴 MANDATORY: Work Validation Protocol
**CRITICAL**: You MUST validate all significant deliverables using work-validator agents before marking tasks as COMPLETED. This is NOT optional.

### When to Validate Work:
1. **After Major Code Changes**: New features, refactoring, architectural changes
2. **Before Task Completion**: All significant deliverables MUST be validated
3. **After Bug Fixes**: Critical and high-impact bug fixes require validation
4. **Before Integration**: Components that integrate with existing systems
5. **After Security Changes**: Any security-related modifications

### Work Validation Selection Criteria:

**Use `work-validator-sonnet` for:**
- Simple/Medium complexity tasks
- Single component changes
- Standard development features
- Quick iteration validation
- Low/Medium business impact

**Use `work-validator-opus` for:**
- Complex/Enterprise projects
- Multi-system integration
- Architecture changes
- Mission-critical components
- High business impact
- Security-related changes
- Performance-critical code

### Mandatory Validation Workflow:
```bash
# MANDATORY SEQUENCE before task completion:
1. Complete implementation/changes
2. Run tests and verify functionality
3. INVOKE WORK-VALIDATOR:
   - Simple tasks: work-validator-sonnet
   - Complex/Critical: work-validator-opus
4. WAIT for validation results
5. IF validation score >= 80: Proceed to git checkpoint
6. IF validation score < 80: Address issues, repeat validation
7. Git checkpoint ONLY after successful validation
```

### Work-Validator Integration Protocol:
```
Task Implementation → Testing → Work-Validator → [Score ≥80] → Git Checkpoint → Task COMPLETED
                                                  ↓ [Score <80]
                                               Fix Issues → Re-validate
```

### ⚠️ VALIDATION ENFORCEMENT RULES:
- **NO TASK** is considered complete without work-validator approval (score ≥80)
- **NO GIT CHECKPOINT** without successful validation
- **ALWAYS SPECIFY** which work-validator to use based on complexity
- **MANDATORY CLEANUP** verification in validation process
- **IF VALIDATION FAILS** multiple times, escalate to work-validator-opus

## 🔴 MANDATORY: Git Checkpoint System
**CRITICAL**: You MUST create Git commits as checkpoints after completing each significant task or subtask. This is NOT optional.

### When to Create Git Checkpoints:
1. **After Work Validation**: IMMEDIATELY after work-validator approval (score ≥80)
2. **After Major Changes**: When you've made significant code changes (new features, refactoring, fixes)
3. **Before Context Switch**: Before moving to a different task or area of the codebase
4. **After Successful Tests**: When tests pass after implementation
5. **After Bug Fixes**: Immediately after fixing any bug or issue

### Git Checkpoint Protocol:
```bash
# MANDATORY SEQUENCE after work validation approval:
1. git add -A                          # Stage all changes
2. git status                          # Verify what will be committed
3. git commit -m "checkpoint: [task-name] - [brief description]
   
   Task ID: [shrimp-task-id if available]
   Validation: PASSED (score: XX/100) by [work-validator-agent]
   Status: COMPLETED
   Changes: [brief summary of changes]
   
   🤖 Generated with Claude Code"       # Create checkpoint
4. git log --oneline -n 5              # Verify commit was created
```

### Checkpoint Commit Message Format:
```
checkpoint: [component/area] - [what was done]

- Task: [specific task completed]
- Validation: PASSED (score: XX/100) by [work-validator-agent]
- Impact: [files/components affected]
- Status: COMPLETED/TESTED/FIXED
- Next: [optional next step if relevant]

🤖 Generated with Claude Code
```

### Example Checkpoint Commits:
```bash
git commit -m "checkpoint: hooks optimization - implemented persistent cache

- Task: Added disk-based credential caching
- Validation: PASSED (score: 87/100) by work-validator-sonnet  
- Impact: credential_provider.py, 22x performance improvement
- Status: COMPLETED and TESTED
- Next: Production deployment ready

🤖 Generated with Claude Code"
```

### ⚠️ ENFORCEMENT RULES:
- **NO TASK** is considered complete without work-validator approval AND Git checkpoint
- **NO CONTEXT SWITCH** without committing validated work
- **ALWAYS VERIFY** commit was created with `git log`
- **NEVER SKIP** validation + checkpoint sequence - they are critical for quality and progress tracking
- **IF USER ASKS** "what did you do?", you can show git log for clear history

## Using Claude Headless Mode for Large Codebase Analysis
When analyzing large codebases or multiple files that might exceed context limits, use Claude in headless mode with the LiteLLM proxy. This leverages Gemini 2.5 models through our secure proxy infrastructure.

### Running Claude Headless Analysis
Use the secure launch script with proxy headless mode for automated analysis:

```bash
# Basic headless analysis with proxy
./scripts/claude-secure-launch.sh --proxy-headless

# With specific analysis tasks (coming soon)
./scripts/claude-analyze.sh "path/to/files" "Your analysis prompt"
```

### Benefits of Claude Headless Mode
- **Secure Integration**: Uses validated LiteLLM proxy with Google Secret Manager
- **Model Flexibility**: Automatically routes to Gemini 2.5 Pro/Flash models
- **Performance**: <2s latency with 100% success rate
- **Fallback Support**: Automatic failover to Vertex AI if needed
- **Memory Integration**: Full access to Cipher and KRAG memory systems

### When to Use Claude Headless Mode
Use Claude headless mode when:
- Analyzing entire codebases or large directories
- Comparing multiple large files
- Needing to understand project-wide patterns or architecture
- Current context window is insufficient for the task
- Requiring integration with workflow orchestration system
- Verifying if specific features, patterns, or security measures are implemented across the codebase

## Workflow Orchestration System
The project includes an advanced workflow orchestration system (`workflows/workflow-orchestrator.js`) that coordinates between subagents and implements Contextual Engineering strategies.

### Key Features:
- **Contextual Engineering**: Implements Write, Select, Compress, and Isolate strategies
- **Pattern Reuse**: Caches and reuses successful workflow patterns
- **Agent Coordination**: Automatically delegates tasks to appropriate subagents
- **Memory Integration**: 
  - Primary agent and orchestrator use Cipher memory
  - Subagents use KRAG Graphiti memory (by design)
- **Performance Optimization**: Token reduction and execution compression

### Workflow Execution:
The orchestrator automatically:
1. Creates workflow context with memory integration
2. Checks for existing patterns to reuse
3. Compresses workflow steps for efficiency
4. Delegates tasks to optimal subagents
5. Stores successful patterns for future use

This system is fully integrated with the validation and git checkpoint protocols defined above.
## Testing - MEDIUM
- Integration test: Use KRAG namespaces for memory isolation
  - Added: 2025-08-08T16:58:17.953478
  - Hash: ee302ac92f9f0023
  - Namespace: session_20250808_165745_primary

## Development - MEDIUM
- Task completion: mcp__shrimp-task-manager__verify_task completed successfully
  - Added: 2025-08-08T17:05:25.062057
  - Hash: 1c66d0be49e8ef19
  - Namespace: session_20250808_170450_primary

## Development - MEDIUM
- Task completion: TodoWrite completed successfully
  - Added: 2025-08-08T17:06:07.103740
  - Hash: 7381c3d28217dfdc
  - Namespace: session_20250808_170532_primary

## Development - MEDIUM
- Task completion: Bash completed successfully
  - Added: 2025-08-16T02:15:53.666915
  - Hash: 40c12efa22ffa87e
  - Namespace: session_20250816_021519_primary

## Development - MEDIUM
- Task completion: Bash completed successfully
  - Added: 2025-08-16T02:19:21.018965
  - Hash: 40c12efa22ffa87e
  - Namespace: session_20250816_021845_primary

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
🔴 MANDATORY: Clean up the repository regularly - remove old reports, cache files, temp files, and obsolete documentation.
🔴 MANDATORY: Work validation (score ≥80) + Git checkpoints after completing tasks - NO EXCEPTIONS.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
🔴 MANDATORY: Clean up the repository regularly - remove old reports, cache files, temp files, and obsolete documentation.