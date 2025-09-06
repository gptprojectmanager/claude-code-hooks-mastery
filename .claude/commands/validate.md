---
allowed-tools: Task, Read, Write, Bash, Grep, Glob
argument-hint: validation_scope
description: Execute comprehensive validation using ensemble methods and 6-gate quality pipeline
---

# Validation Command

Esegui validazione completa del progetto utilizzando ensemble validation, 6-gate pipeline, e collective intelligence.

## Variables

- **SCOPE**: $ARGUMENTS or "full_project" if not specified
  - Scope di validazione (es. "recent_changes", "security_only", "performance_focus")
  - Used by: validation agent ensemble

## Validation Ensemble

### Core Validation Agents
- @agent-work-validator-opus (comprehensive quality assessment)
- @agent-code-reviewer-opus (code quality e security)
- @agent-security-auditor-opus (vulnerability assessment)
- @agent-tester-debugger-sonnet (testing completeness)

### Specialized Validators (conditional)
- @agent-performance-engineer-opus (performance analysis)
- @agent-browser-automation-agent-opus (UI/UX validation)
- @agent-cleanup-validator-opus (system hygiene)

## 6-Gate Validation Pipeline

### Gate 1: Code Quality (20 points)
```
- Code style e conventions compliance
- Architecture pattern adherence  
- Documentation completeness
- Naming conventions e readability
```

### Gate 2: Security Assessment (20 points)
```
- Vulnerability scanning (OWASP Top 10)
- Secret/credential exposure check
- Input validation e sanitization
- Authentication/authorization review
```

### Gate 3: Testing Coverage (20 points)
```
- Unit test coverage (≥80% target)
- Integration test presence
- E2E test completeness
- Test quality e maintainability
```

### Gate 4: Performance Analysis (15 points)
```
- Load time optimization
- Memory usage efficiency
- CPU utilization patterns
- Database query optimization
```

### Gate 5: Compatibility & Standards (15 points)
```
- Cross-browser compatibility
- Mobile responsiveness  
- Accessibility compliance (WCAG)
- API contract adherence
```

### Gate 6: Deployment Readiness (10 points)
```
- Environment configuration
- Dependency management
- Monitoring e logging setup
- Rollback procedure defined
```

## Execution Instructions

1. **Scope Analysis**
   - Determina validation scope in base a $ARGUMENTS
   - Identifica quale subset di agents attivare
   - Setup validation parameters e thresholds

2. **Ensemble Validation Phase**
   - Esegui validation agents in parallel
   - Collect individual assessments e scores
   - Cross-validate findings tra diversi agents

3. **Collective Intelligence Synthesis**
   - Aggregate scores utilizzando ensemble methods
   - Identify consensus issues e outlier findings
   - Calculate confidence intervals per each assessment

4. **Gate Scoring & Reporting**
   - Score ogni gate su 100 point scale
   - Identify critical failures (score <70)
   - Generate detailed remediation plans

## Validation Scopes

### Full Project Validation
```
- All 6 gates con complete agent ensemble
- Comprehensive cross-domain analysis
- Production readiness assessment
```

### Recent Changes Validation
```
- Focus su git diff changes
- Relevant gates based on change type
- Impact assessment e regression check
```

### Security-Only Validation
```
- Security auditor + code reviewer focus
- Gate 2 (Security) emphasis
- Vulnerability prioritization
```

### Performance-Focus Validation
```
- Performance engineer + work validator
- Gate 4 (Performance) deep dive
- Optimization recommendations
```

## Output Format

Crea structured validation report:

```
validation_results/
└── validation_<timestamp>/
    ├── agent_reports/        # Individual agent assessments
    ├── gate_scores/         # 6-gate detailed scores
    ├── ensemble_analysis/   # Collective intelligence synthesis
    ├── critical_issues/     # High-priority failures
    ├── recommendations/     # Remediation action plans
    └── executive_summary/   # Management-ready report
```

## Scoring System

### Individual Gate Scores
- **90-100**: Excellent (✅ Production Ready)
- **80-89**: Good (⚠️ Minor improvements needed)
- **70-79**: Adequate (🔄 Moderate issues)
- **60-69**: Poor (❌ Major improvements required)
- **<60**: Critical (🚨 Blocking issues)

### Overall Validation Score
- **Weighted Average**: Gate scores con domain-specific weights
- **Confidence Interval**: Statistical confidence nella assessment
- **Risk Level**: LOW/MEDIUM/HIGH based on critical issues

## Success Criteria

- **Overall Score**: ≥85/100 for production deployment
- **Critical Issues**: Zero blocking security vulnerabilities
- **Gate Coverage**: All relevant gates scored ≥70
- **Consensus**: ≥80% agent agreement on major issues

## Report

Al completamento fornisci:
- Overall validation score con confidence interval
- Gate-by-gate detailed breakdown
- Critical issues priority list
- Remediation timeline estimates
- Production readiness recommendation