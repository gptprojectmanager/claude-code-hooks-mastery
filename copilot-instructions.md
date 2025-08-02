# Copilot Code Review Instructions

## Review Focus Areas
- Security vulnerabilities and best practices
- Performance optimizations and bottlenecks  
- Code maintainability and readability
- Error handling and edge cases
- Type safety and documentation quality

## Project-Specific Guidelines
- Follow PEP 8 for Python code
- Use type hints consistently
- Ensure comprehensive test coverage
- Document public APIs thoroughly
- Validate input parameters

## Multi-Agent System Context
- This repository contains a Claude Code multi-agent system
- Focus on agent orchestration patterns and tool integration
- Validate MCP server configurations and security
- Review hook implementations for safety
- Check task management and cleanup mechanisms

## Review Criteria
- Rate security: 1-10 (8+ required)
- Rate performance: 1-10 (7+ required)  
- Rate maintainability: 1-10 (8+ required)
- Flag any breaking changes
- Suggest optimizations where applicable

## Special Attention Areas
- `.claude/agents/` - Agent configurations and prompts
- `.claude/hooks/` - Security and validation hooks
- `.claude/settings.json` - Tool permissions and configurations
- Multi-agent workflow patterns and delegation logic