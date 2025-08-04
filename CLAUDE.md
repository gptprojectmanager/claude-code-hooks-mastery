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

## Using Gemini CLI for Large Codebase Analysis
When analyzing large codebases or multiple files that might exceed context limits, use the Gemini CLI with its massive context window. Use `gemini -p` to leverage Google Gemini's large context capacity.

### File and Directory Inclusion Syntax
Use the `@` syntax to include files and directories in your Gemini prompts. The paths should be relative to WHERE you run the gemini command.

#### Examples:
**Single file analysis:**
```bash
gemini -p " @src/main.py Explain this file's purpose and structure"
```

**Multiple files:**
```bash
gemini -p " @.observability/client/package.json @src/index.js Analyze the dependencies used in the code"
```

**Entire directory:**
```bash
gemini -p " @.observability/client/src/App.vue Summarize the architecture of this codebase"
```

**Current directory and subdirectories:**
```bash
gemini -p " @./** Give me an overview of this entire project"
```
Or use `--all_files` flag:
```bash
gemini --all_files -p "Analyze the project structure and dependencies"
```

### When to Use Gemini CLI
Use `gemini -p` when:
- Analyzing entire codebases or large directories
- Comparing multiple large files
- Needing to understand project-wide patterns or architecture
- Current context window is insufficient for the task
- Verifying if specific features, patterns, or security measures are implemented across the codebase.