# Primary Agent OpenEvolve Integration

## Agenti Specializzati - Sezione da Aggiungere

### OpenEvolve & Evolutionary Optimization Specialists
- **OpenEvolve-Optimizer**: Ottimizzazione evolutiva del codice tramite Gemini + OpenEvolve
  - **Triggers**: "ottimizza codice", "evolutionary optimization", "performance improvement"
  - **Capabilities**: Git worktrees, iteration selection, multi-stage validation
  - **Tools**: OpenEvolve API, LiteLLM Gemini, KRAG Memory, performance benchmarking

## Trigger Recognition - Sezione da Aggiungere

### Code Optimization Triggers
```
Automatic delegation to openevolve-optimizer-opus when:
- User mentions: "ottimizza codice", "migliorare performance", "evolutionary optimization"
- Code contains: nested loops, O(n²) algorithms, inefficient patterns
- Performance bottlenecks identified requiring code-level optimization
- Explicit OpenEvolve/Gemini optimization requests
```

## Git Worktree Management - Sezione da Aggiungere

### Parallel Execution with Git Worktrees
```bash
# Create isolated optimization workspace
git worktree add ../optimization_workspace_{timestamp} -b optimization/{timestamp}_{language}

# Multiple instances coordination
INSTANCE_1_PORT=4001  # LiteLLM proxy
INSTANCE_2_PORT=8000  # OpenEvolve service

# Service startup commands
./start_openevolve_gemini_service.sh  # Avvia LiteLLM + OpenEvolve
```

### Worktree Cleanup Protocol
```bash
# After optimization completion
git worktree remove ../optimization_workspace_{timestamp}
git branch -D optimization/{timestamp}_{language}
```

## Service Management - Sezione da Aggiungere

### OpenEvolve Infrastructure Commands
```bash
# Health checks
curl http://localhost:8000/health  # OpenEvolve service
curl http://localhost:4001/models  # LiteLLM proxy

# Service startup
cd /Users/sam/claude-code-hooks-mastery/.claude/utils
./start_openevolve_gemini_service.sh

# Service logs monitoring
tail -f litellm_gemini.log openevolve_service.log
```

## Agent Routing Table - Sezione da Aggiungere

### Code Optimization Routing
| Request Type | Agent | Prerequisites |
|-------------|-------|---------------|
| "ottimizza codice" | openevolve-optimizer-opus | Services running + KRAG namespace |
| "evolutionary optimization" | openevolve-optimizer-opus | Git worktree + LiteLLM proxy |
| "performance improvement" | openevolve-optimizer-opus | OpenEvolve service + Gemini credits |
| Complex algorithmic optimization | openevolve-optimizer-opus + language-specialist | Multi-agent coordination |

## KRAG Memory Zones - Sezione da Aggiungere

### OpenEvolve Memory Namespacing
```
KRAG Group IDs for OpenEvolve:
├── openevolve_optimization_{session_id}     # Active optimization session
├── openevolve_patterns_validated           # Proven optimization patterns  
├── openevolve_performance_baselines        # Performance comparison data
├── openevolve_credit_analytics             # Gemini credit usage tracking
└── openevolve_service_config              # Service status and configuration
```

## Workflow Integration - Sezione da Aggiungere

### OpenEvolve Delegation Pattern
```
Primary-Agent detects optimization request
    ↓
Check services status (LiteLLM + OpenEvolve)
    ↓
Create KRAG namespace: openevolve_optimization_{timestamp}
    ↓
Create HANDOFF_TOKEN for openevolve-optimizer-opus
    ↓  
Setup git worktree for isolated execution
    ↓
Delegate to openevolve-optimizer-opus with:
  - Code to optimize
  - Performance objectives
  - Credit budget constraints
  - Validation requirements
    ↓
Monitor progress via KRAG token + Shrimp tasks
    ↓
Validate results via work-validator-opus
    ↓
Integrate optimized code + cleanup worktree
```

## Error Handling - Sezione da Aggiungere

### OpenEvolve Failure Recovery
- **Services Down**: Auto-start via start_openevolve_gemini_service.sh
- **Git Worktree Conflicts**: Create new timestamped worktree
- **Optimization Failures**: Retry with reduced iteration count
- **Credit Exhaustion**: Graceful degradation with simpler optimization
- **Validation Failures**: Rollback + manual review escalation