# Gemini CLI Orchestration Patterns

## Pattern Analysis & Optimal Implementation

### **Pattern A: Subagent-Driven Gemini CLI Delegation**
```
Primary-Agent → Subagent → [Gemini CLI Analysis] → Subagent Processing → Deliverable
```

**Workflow:**
1. Primary-agent delegates task to specialist subagent
2. Subagent recognizes need for large-context analysis
3. Subagent calls safe Gemini CLI wrapper
4. Gemini CLI provides comprehensive analysis
5. Subagent processes and validates Gemini response  
6. Subagent produces final deliverable incorporating Gemini insights
7. Deliverable goes to work-validator for final validation

**Use Cases:**
- Code-reviewer analyzing large codebase
- Security-specialist conducting comprehensive security audit
- Backend-architect understanding complex system architecture
- Data-engineer analyzing large data pipeline systems

**Advantages:**
- ✅ Specialist maintains full control over analysis
- ✅ Domain expertise applied to Gemini insights
- ✅ Contextual interpretation of large-scale analysis
- ✅ Maintains subagent specialization

**Disadvantages:**
- ❌ Requires Gemini CLI safety integration in each subagent
- ❌ Potential for inconsistent Gemini usage patterns
- ❌ Harder to centralize safety monitoring

### **Pattern B: Validator-Driven Gemini CLI Assessment**
```
Primary-Agent → Subagent → Deliverable → Work-Validator → [Gemini CLI Analysis] → Score → Primary-Agent
```

**Workflow:**
1. Primary-agent delegates task to specialist subagent
2. Subagent produces deliverable using standard tools
3. Work-validator receives deliverable for assessment
4. Work-validator uses Gemini CLI for comprehensive validation
5. Gemini CLI provides large-context quality assessment
6. Work-validator generates score and recommendations
7. Primary-agent makes approval/revision decision

**Use Cases:**
- Quality validation of complex implementations
- Cross-referencing deliverable against large codebase context
- Comprehensive compliance checking
- Large-scale integration impact assessment

**Advantages:**
- ✅ Centralized safety control for all Gemini CLI usage
- ✅ Consistent validation methodology across all subagents
- ✅ Specialist focus on core competency, not Gemini integration
- ✅ Enhanced security through centralized monitoring

**Disadvantages:**
- ❌ Validator may lack domain-specific expertise for analysis
- ❌ Potential disconnect between specialist knowledge and validation
- ❌ Less contextual understanding during analysis phase

## **🎯 Optimal Solution: Hybrid Intelligent Pattern**

### **Hybrid Pattern: Context-Aware Dual Usage**
```
Primary-Agent → [Intelligence Router] → Optimal Pattern Selection → Execution → Validation
```

**Implementation Strategy:**

#### **Phase 1: Task Analysis** (Primary-Agent)
```json
{
  "task_classification": {
    "complexity": "simple/medium/complex/enterprise",
    "scope": "single_file/component/system/codebase",
    "requires_large_context": "boolean",
    "domain_expertise_critical": "boolean"
  },
  "gemini_strategy": "subagent_driven/validator_driven/hybrid"
}
```

#### **Phase 2: Pattern Selection Logic**

**Use Pattern A (Subagent-Driven) When:**
- Task requires deep domain expertise + large context
- Complex analysis needs specialist interpretation
- Examples: Architecture analysis, Security audit, Performance optimization

**Use Pattern B (Validator-Driven) When:**
- Task is complete, needs quality validation
- Cross-referencing against large codebase required
- Examples: Code quality assessment, Compliance checking, Integration validation

**Use Hybrid When:**
- Both analysis and validation benefit from large context
- Critical tasks requiring maximum quality assurance

### **🔧 Implementation Architecture**

#### **Enhanced Primary-Agent Intelligence Router**
```python
def determine_gemini_strategy(task_spec):
    """
    Intelligent routing for optimal Gemini CLI usage pattern
    """
    if task_spec.requires_large_context and task_spec.domain_expertise_critical:
        if task_spec.task_type in ["architecture_analysis", "security_audit", "performance_analysis"]:
            return "subagent_driven"
        elif task_spec.task_type in ["code_review", "quality_validation", "compliance_check"]:
            return "validator_driven"
        else:
            return "hybrid"
    else:
        return "standard_workflow"
```

#### **Pattern A Implementation: Subagent-Driven**
```bash
# Code-Reviewer with Gemini CLI delegation
code-reviewer receives task
  ↓
code-reviewer: "Need large context analysis for comprehensive review"
  ↓
code-reviewer executes: python3 .claude/scripts/safe-gemini-wrapper.py $CODEBASE "ANALYZE ONLY: Assess code quality, patterns, security issues"
  ↓
code-reviewer processes Gemini insights with domain expertise
  ↓
code-reviewer produces comprehensive review deliverable
  ↓
work-validator validates final deliverable (without re-analyzing full codebase)
```

#### **Pattern B Implementation: Validator-Driven**
```bash
# Standard subagent work + comprehensive validation
python-pro produces optimized code
  ↓
work-validator receives deliverable
  ↓
work-validator: "Need to validate against large codebase context"
  ↓
work-validator executes: python3 .claude/scripts/safe-gemini-wrapper.py $CODEBASE "ANALYZE ONLY: Validate this deliverable against codebase patterns and quality standards"
  ↓
work-validator generates comprehensive validation score
  ↓
primary-agent makes approval decision based on validation
```

#### **Hybrid Implementation: Dual Analysis**
```bash
# Critical tasks requiring maximum quality
backend-architect receives complex API design task
  ↓
backend-architect uses Gemini CLI: "ANALYZE ONLY: Understand existing API patterns and architecture"
  ↓
backend-architect produces API design incorporating Gemini insights
  ↓
work-validator uses Gemini CLI: "ANALYZE ONLY: Validate this API design against full system architecture"
  ↓
primary-agent receives both specialist deliverable + comprehensive validation
```

## **🎯 Decision Matrix**

| Task Type | Complexity | Context Needed | Pattern | Rationale |
|-----------|------------|----------------|---------|-----------|
| Code Review | High | Full Codebase | A (Subagent-Driven) | Domain expertise crucial for interpreting large-scale issues |
| Security Audit | High | Full System | A (Subagent-Driven) | Security specialist needs full context for threat modeling |
| Architecture Design | High | Existing System | Hybrid | Both analysis and validation benefit from large context |
| Code Implementation | Medium | Component Level | B (Validator-Driven) | Focus on implementation, validate against broader context |
| Bug Fix | Low | Local Context | Standard | No Gemini CLI needed |
| Quality Check | Medium | Codebase Patterns | B (Validator-Driven) | Validation against established patterns |

## **🚀 Implementation Roadmap**

### **Phase 1: Pattern A (Subagent-Driven)**
- ✅ Integrate safe Gemini CLI wrapper in key subagents
- ✅ Update code-reviewer, security-specialist, backend-architect
- ✅ Implement intelligent Gemini delegation logic

### **Phase 2: Pattern B (Validator-Driven)**  
- ✅ Enhance work-validator with Gemini CLI integration
- ✅ Implement comprehensive validation scoring
- ✅ Create validation-specific Gemini prompts

### **Phase 3: Hybrid Intelligence**
- 🔄 Implement primary-agent intelligence router
- 🔄 Create task classification logic
- 🔄 Add pattern selection automation

### **Phase 4: Optimization**
- 🔄 Monitor pattern effectiveness
- 🔄 Optimize Gemini prompt templates
- 🔄 Enhance safety monitoring

## **📊 Expected Benefits**

### **Quality Improvements:**
- 🎯 **40-60% better context understanding** for complex tasks
- 🎯 **Reduced false positives** in security and quality assessments  
- 🎯 **Enhanced architecture decisions** with full system awareness

### **Efficiency Gains:**
- ⚡ **Faster large codebase analysis** (minutes vs hours)
- ⚡ **Reduced back-and-forth iterations** between subagents
- ⚡ **Comprehensive validation** without manual codebase traversal

### **Safety Assurance:**
- 🛡️ **Zero file modification risk** with safe wrapper
- 🛡️ **Centralized monitoring** of all Gemini CLI usage
- 🛡️ **Audit trail** for compliance and debugging

## **🔐 Architettura di Sicurezza del Wrapper (`safe-gemini-wrapper.py`)**

La garanzia di "Zero file modification risk" non è una funzionalità nativa di Gemini CLI, ma è implementata attraverso uno script wrapper personalizzato che impone un ambiente di esecuzione "sola lettura" di fatto. Questo wrapper agisce come un gatekeeper di sicurezza prima di ogni chiamata a Gemini CLI, basandosi su tre livelli di protezione:

### 1. Validazione Semantica del Prompt
Prima di eseguire qualsiasi comando, il wrapper analizza il prompt per prevenire operazioni di scrittura.
- **Whitelist (Prefissi Obbligatori)**: Il prompt **deve** iniziare con un prefisso sicuro come `ANALYZE ONLY - DO NOT MODIFY`, `DESCRIBE ONLY`, o `ASSESS ONLY`. Se il prefisso manca, l'operazione viene bloccata.
- **Blacklist (Parole Chiave Pericolose)**: Il wrapper cerca attivamente parole chiave che implicano una modifica, come `fix`, `implement`, `create`, `write`, `delete`, `refactor`, ecc. Se una di queste parole viene trovata, l'esecuzione viene interrotta.

### 2. Verifica di Integrità tramite Hashing dei File
Per garantire che nessun file venga alterato, il wrapper utilizza un sistema di hashing.
- **Pre-analisi**: Calcola un hash SHA256 aggregato di tutti i file nel percorso specificato (escludendo `.git`).
- **Post-analisi**: Ricalcola l'hash dopo che Gemini CLI ha terminato.
- **Confronto**: Se i due hash non corrispondono, significa che è avvenuta una modifica. Questo attiva immediatamente la procedura di rollback.

### 3. Backup e Rollback Atomico con Git
Come ultima linea di difesa, il wrapper sfrutta Git per garantire che il repository possa essere ripristinato a uno stato noto.
- **Backup**: Prima dell'analisi, esegue `git add -A` e `git commit` per creare un punto di ripristino sicuro.
- **Rollback**: Se la verifica di hashing fallisce, il wrapper esegue automaticamente `git checkout -- .` e `git clean -fd` per annullare qualsiasi modifica ai file e rimuovere eventuali file creati, riportando il repository allo stato esatto del backup.

Questa architettura a più livelli garantisce che, anche in caso di comportamento inaspettato di Gemini CLI, il sistema degli agenti possa utilizzarlo per analisi su larga scala senza alcun rischio di modifiche non autorizzate o accidentali alla codebase.