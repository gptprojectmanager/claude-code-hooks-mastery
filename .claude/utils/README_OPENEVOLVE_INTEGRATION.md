# OpenEvolve Integration System

## Overview

This integration system enables evolutionary code optimization using OpenEvolve with Gemini models, featuring:
- **Parallel Execution**: Git worktrees for concurrent optimization sessions
- **Intelligent Iteration Selection**: Complexity-based optimization parameters  
- **Comprehensive Validation**: Multi-stage quality gates
- **Seamless Agent Integration**: Works with existing Claude Code agent ecosystem

## Components

### 1. OpenEvolve Optimizer Agent (`openevolve-optimizer-opus.md`)
- Specialized Opus agent for complex optimization decisions
- Integrates with OpenEvolve REST API service
- Manages entire optimization workflow
- Coordinates with other agents in ecosystem

### 2. Git Worktree Manager (`openevolve_worktree_manager.py`)
- Creates isolated workspaces for parallel optimization
- Manages session lifecycle and cleanup
- Handles branch creation and merging
- Prevents conflicts between concurrent sessions

### 3. CLI Interface (`openevolve_cli.sh`)
- Simple command-line interface for optimization workflows
- Health checks and service monitoring
- Session management and cleanup utilities

### 4. Demo System (`openevolve_test_demo.py`)
- Complete workflow demonstration
- Integration testing capabilities
- Performance validation examples

## Quick Start

### Prerequisites

1. **OpenEvolve Service Running**:
   ```bash
   cd /Users/sam/openevolve/apps/openevolve-service
   ./start.sh
   ```

2. **LiteLLM Proxy** (for Gemini access):
   ```bash
   litellm --config litellm_config.yaml --port 4001
   ```

3. **Google API Key** configured for Gemini access

### Usage Examples

#### Basic Optimization
```bash
# Optimize a Python file
./openevolve_cli.sh optimize my_code.py python

# Check service health
./openevolve_cli.sh health

# List active sessions
./openevolve_cli.sh list
```

#### Agent Integration
```python
# From within Claude Code agent
from openevolve_worktree_manager import OpenEvolveWorktreeManager

manager = OpenEvolveWorktreeManager()
success, message, session = manager.create_optimization_session(
    code=code_to_optimize,
    language="python",
    optimization_params={"iterations": 25}
)
```

#### Demo Workflow
```bash
# Run complete optimization demo
./openevolve_cli.sh demo
```

## Architecture

### Parallel Execution Flow
```
Main Repo (claude-code-hooks-mastery)
├── worktree_1 (optimization/python_abc123_1234567890)
├── worktree_2 (optimization/python_def456_1234567891)  
└── worktree_3 (optimization/python_ghi789_1234567892)
```

### Session Lifecycle
1. **Creation**: Isolated worktree + branch creation
2. **Optimization**: OpenEvolve evolutionary process  
3. **Validation**: Multi-stage quality gates
4. **Integration**: Merge results or cleanup
5. **Cleanup**: Remove worktree and temporary branches

### Agent Orchestration
```
Primary Agent → OpenEvolve Optimizer Agent
                      ↓
              Git Worktree Creation
                      ↓
              OpenEvolve Service → Gemini Models
                      ↓
              Quality Validation Pipeline
                      ↓
              Result Integration → Completion
```

## Configuration

### Iteration Selection Algorithm
- **Simple Code** (< 50 lines): 5-10 iterations
- **Medium Complexity** (50-200 lines): 10-25 iterations  
- **Complex Algorithms** (200+ lines): 25-50 iterations
- **Nested Loop Adjustment**: +15 iterations for complexity ≥ 2

### Quality Gates
1. **Syntax Validation**: Compilation/parsing check
2. **Test Compatibility**: Existing tests still pass  
3. **Performance Benchmark**: Measurable improvement
4. **Code Quality**: Maintainability metrics
5. **Security Analysis**: No new vulnerabilities
6. **Behavioral Equivalence**: Functional correctness

### Concurrent Sessions
- **Maximum**: 5 parallel optimization sessions
- **Timeout**: 24 hours for stale session cleanup
- **Isolation**: Complete workspace separation
- **Resource Management**: Automatic cleanup on completion

## Integration Points

### Primary Agent Integration
- Triggered by optimization keywords: "ottimizza codice", "evolutionary optimization" 
- KRAG memory for context preservation
- Shrimp task manager for workflow tracking
- Handoff protocols with language specialists

### Language Specialist Coordination
- **Python-Pro-Sonnet**: Domain expertise for Python optimizations
- **JavaScript-Pro-Sonnet**: V8-specific optimizations
- **Code-Reviewer-Opus**: Quality assurance and review
- **Security-Auditor-Opus**: Security validation

## Troubleshooting

### Service Issues
```bash
# Check service health
curl http://localhost:8000/health

# View service logs  
cd /Users/sam/openevolve/apps/openevolve-service
docker-compose logs -f
```

### Session Issues  
```bash
# List active sessions
./openevolve_cli.sh list

# Check specific session
./openevolve_cli.sh status SESSION_ID

# Cleanup stale sessions
./openevolve_cli.sh cleanup-stale
```

### Git Worktree Issues
```bash
# List all worktrees
git worktree list

# Force remove problematic worktree  
git worktree remove path/to/worktree --force
```

## Performance Metrics

### Expected Improvements
- **Algorithmic**: O(n²) → O(n log n) transformations
- **Performance**: 15-50% execution time reduction
- **Memory**: 10-30% memory footprint improvement  
- **Quality**: Maintained or improved readability

### Credit Optimization
- **Smart Iterations**: Complexity-based selection prevents waste
- **Early Stopping**: Plateau detection saves credits
- **Parallel Efficiency**: Multiple optimizations without extra overhead
- **ROI Tracking**: Cost-benefit analysis per optimization type

## Future Enhancements

1. **Multi-Language Support**: Extend beyond Python/JavaScript
2. **Custom Evaluators**: Domain-specific optimization metrics
3. **Real-time Monitoring**: WebUI for optimization progress
4. **ML-Based Selection**: Learn optimal iteration counts from history  
5. **Distributed Execution**: Scale across multiple machines

This system provides production-ready evolutionary code optimization that maximizes Gemini credit utilization while delivering consistently high-quality results.