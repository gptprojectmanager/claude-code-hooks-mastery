---
allowed-tools: Task, Read, Write, Bash, Grep, Glob
argument-hint: file_or_directory_path
description: Trigger evolutionary code optimization using OpenEvolve with comprehensive performance analysis
---

# Code Optimization Command

Attiva il sistema OpenEvolve per ottimizzazione evolutiva del codice con analisi delle performance e validazione multi-livello.

## Variables

- **TARGET**: $ARGUMENTS or current working directory if not specified
  - File o directory da ottimizzare (es. src/algorithm.py, src/components/)
  - Used by: openevolve-optimizer-opus agent

## Execution Instructions

1. **Analysis Phase**
   - Analizza complessità del codice target
   - Identifica bottlenecks e pattern di ottimizzazione
   - Stima iterations necessarie per OpenEvolve

2. **Preparation Phase**  
   - Verifica disponibilità LiteLLM proxy (port 4001)
   - Setup git worktree per isolation
   - Prepara environment per optimization

3. **Optimization Phase**
   - Attiva @agent-openevolve-optimizer-opus
   - Esegui optimization evolutiva iterativa
   - Monitora progress e performance metrics

4. **Validation Phase**
   - 6-gate validation pipeline
   - Performance benchmarking 
   - Security e quality checks
   - Backward compatibility verification

## Agent Orchestration

### Primary Optimization Agent
- @agent-openevolve-optimizer-opus (TARGET optimization)

### Supporting Validation Agents
- @agent-work-validator-opus (quality validation)
- @agent-performance-engineer-opus (benchmarking)
- @agent-security-auditor-opus (security review)

## Output Format

Crea directory structure organizzata:

```
optimization_results/
└── optimization_<timestamp>/
    ├── original/              # Backup codice originale
    ├── iterations/            # Iterazioni evolutive
    │   ├── iteration_1/
    │   ├── iteration_2/
    │   └── iteration_N/
    ├── benchmarks/           # Performance metrics
    ├── validation/           # Quality gates results
    └── final/               # Codice ottimizzato finale
```

## Success Criteria

- **Performance**: Miglioramento 15-50% execution time
- **Memory**: Riduzione 10-30% memory usage  
- **Quality**: Score ≥92/100 validation
- **Security**: Zero vulnerabilities introdotte
- **Compatibility**: 100% test suite pass

## Report

Al completamento fornisci:
- Path alla directory optimization_results/
- Performance improvement percentages
- Validation scores per ogni gate
- Summary delle optimizations applicate
- Raccomandazioni per deployment