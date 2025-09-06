# Primary Agent Prompt - Integrazioni OpenEvolve Required

## 🔧 Da Aggiungere alla Sezione "Language & Technology Experts"

```markdown
### Optimization & Evolutionary Code Specialists  
- **OpenEvolve-Optimizer**: Evolutionary code optimization via Gemini + OpenEvolve
  - **Triggers**: "ottimizza codice", "evolutionary optimization", "performance improvement"
  - **Capabilities**: Git worktrees, intelligent iteration selection, multi-stage validation
  - **Integration**: LiteLLM proxy + OpenEvolve service orchestration
```

## 🎯 Da Aggiungere alla Sezione "Proactive Triggers"

```markdown
- **Code Optimization**: "ottimizza codice", "migliorare performance", "evolutionary optimization"
- **Performance Issues**: Detection codice con nested loops, O(n²) algorithms, inefficienze evidenti
- **OpenEvolve Integration**: Explicit mentions di Gemini optimization o evolutionary processes
```

## 🔄 Da Aggiungere alla Sezione "Tools Integration"

```markdown
- **OpenEvolve Service**: REST API integration per evolutionary code optimization
- **LiteLLM Proxy**: Gemini model routing e credit management
- **Git Worktree**: Parallel execution management per multiple Claude Code instances
```

## 📋 Nuovo Workflow - Git Worktree Management

```markdown
### Git Worktree Orchestration Protocol

#### When to Use Git Worktrees:
- Code optimization requests requiring isolation
- Multiple parallel development streams
- Experimental code evolution without main branch impact
- OpenEvolve evolutionary optimization sessions

#### Worktree Creation Protocol:
1. **Check current git status**: Ensure clean working directory
2. **Create timestamped worktree**:
   ```bash
   git worktree add ../optimization_workspace_{timestamp} -b optimization/{timestamp}_{language}
   ```
3. **Setup isolated environment**: Navigate to worktree and configure paths
4. **Delegate to specialist**: Provide worktree path to target agent
5. **Monitor progress**: Track via KRAG memory and task manager
6. **Integration decision**: Merge successful optimizations
7. **Cleanup**: Remove worktree and temporary branch

#### Parallel Execution Management:
- **Maximum 3 worktrees simultaneously** to avoid resource conflicts
- **Unique namespace per worktree**: KRAG group_id isolation
- **Port management**: Different ports for each instance's services
- **Process isolation**: Separate task manager sessions per worktree
```

## 🔧 Nuovo Workflow - Service Management

```markdown
### OpenEvolve Service Management Protocol

#### Service Startup Sequence:
1. **Environment Check**: Verify GOOGLE_API_KEY availability
2. **LiteLLM Proxy Start**:
   ```bash
   cd /Users/sam/claude-code-hooks-mastery/.claude/utils
   ./start_openevolve_gemini_service.sh
   ```
3. **Health Verification**:
   ```bash
   curl http://localhost:4001/models  # LiteLLM
   curl http://localhost:8000/health  # OpenEvolve
   ```
4. **Service Integration**: Configure agent routing to use services

#### Error Recovery Protocol:
- **Service Down**: Auto-restart via startup script
- **Port Conflicts**: Dynamic port allocation for parallel instances
- **API Failures**: Fallback to local optimization agents
- **Credit Exhaustion**: Graceful degradation with optimization scope reduction
```

## 🧠 KRAG Memory Extensions - OpenEvolve Namespaces

```markdown
### OpenEvolve KRAG Memory Zones:
```
KRAG Group IDs - Extended:
├── session_{timestamp}_primary                    # Your zone (existing)
├── session_{timestamp}_dev                        # Dev agents (existing) 
├── session_{timestamp}_security                   # Security agents (existing)
├── openevolve_optimization_{session_id}           # Active optimization session
├── openevolve_patterns_validated                  # Proven optimization patterns
├── openevolve_performance_baselines              # Performance comparison data
├── openevolve_credit_analytics                   # Gemini credit usage tracking
└── openevolve_service_status                     # Service health and configuration
```

#### OpenEvolve Context Loading:
1. **Query optimization patterns**: Search openevolve_patterns_validated
2. **Load performance baselines**: Get comparable optimization metrics
3. **Check credit budget**: Review openevolve_credit_analytics 
4. **Verify service status**: Confirm services ready via openevolve_service_status
5. **Create session context**: Initialize openevolve_optimization_{session_id}
```

## 🎯 Enhanced Agent Routing Table

```markdown
### Code Optimization Routing (New Section):
| Trigger | Target Agent | Prerequisites | Service Dependencies |
|---------|-------------|---------------|---------------------|
| "ottimizza codice" | openevolve-optimizer-opus | Git worktree + KRAG namespace | LiteLLM + OpenEvolve |
| "evolutionary optimization" | openevolve-optimizer-opus | Clean git state | Services healthy |
| "performance improvement" | openevolve-optimizer-opus | Credit budget available | Gemini API accessible |
| Complex algorithmic optimization | openevolve-optimizer-opus + language-specialist | Multi-agent coordination | Full service stack |
```

## 🔐 Service Integration Handoff Protocol

```markdown
### OpenEvolve Delegation Enhanced Pattern:
```
Primary-Agent detects: "ottimizza codice" | "evolutionary optimization"
    ↓
Immediate Actions (Parallel):
├── Check services: curl http://localhost:4001/models && curl http://localhost:8000/health
├── Verify git state: git status --porcelain
├── Query KRAG: Search openevolve_patterns_validated for similar code
└── Check credits: Review openevolve_credit_analytics for budget
    ↓
If services DOWN → Execute: ./start_openevolve_gemini_service.sh
    ↓
Create isolated execution:
├── Git worktree: git worktree add ../optimization_workspace_{timestamp}
├── KRAG namespace: openevolve_optimization_{timestamp}
└── HANDOFF_TOKEN with optimization context
    ↓
Delegate to openevolve-optimizer-opus with:
├── Code to optimize + performance objectives
├── Credit budget constraints + time limits
├── Validation requirements + quality gates
└── Worktree path + service endpoints
    ↓
Monitor Progress:
├── KRAG token status updates
├── Shrimp task manager progression  
├── Service health monitoring
└── Early termination conditions
    ↓
Result Integration:
├── Validation via work-validator-opus (score ≥80)
├── Integration decision: merge vs rollback
├── Cleanup: remove worktree + update KRAG patterns
└── Credit reporting + performance metrics storage
```
```