# 🧠 Team Development Guide - Claude Code Multi-Agent System

## 📋 Panoramica

Questa guida completa documenta il processo di sviluppo, miglioramento e creazione di nuovi agenti per il sistema multi-agente Claude Code. Contiene tutti i riferimenti, repository, file e best practices necessari per future iterazioni del team.

## 🎯 Obiettivo del Sistema

Costruire un team di sub-agenti specializzati per automatizzare compiti di sviluppo software professionale, con orchestrazione intelligente, memoria persistente e capabilities enterprise-level.

## 🆕 **Aggiornamenti Recenti (Agosto 2025)**

### Correzioni e Stabilizzazione del Workflow GitHub Copilot
Il workflow di revisione automatica con GitHub Copilot (`.github/workflows/copilot-review.yml`) è stato reso stabile attraverso una serie di correzioni critiche:
- **Sintassi YAML Corretta**: Risolto un errore di sintassi che impediva l'esecuzione del workflow.
- **Gestione Eventi Push/PR**: Il workflow ora si attiva correttamente sia su `push` verso branch protetti che su `pull_request`, eseguendo i passaggi di revisione solo quando è presente una PR.
- **Installazione GitHub CLI**: L'installazione della CLI di GitHub è stata spostata in uno step dedicato per garantirne la disponibilità a tutti i passaggi successivi.
- **Contesto di Esecuzione**: Impostata la `working-directory` per i comandi `gh` per risolvere l'errore "not a git repository".
- **Gestione Label (Rimosso)**: Lo step che aggiungeva label è stato rimosso per evitare errori dovuti a label non esistenti nel repository, semplificando il processo.
- **Risoluzione Conflitti di Merge**: Aggiornata la branch con le modifiche dal repository `upstream`, risolvendo conflitti e mantenendo la coerenza della codebase.
- **Correzione Prompt Agente**: Il prompt dell'agente `github-copilot-reviewer` è stato allineato al workflow reale per garantire che le sue azioni siano corrette e prevedibili.

### Sistema Dual-Review GitHub Copilot Implementato
- **File**: `.claude/agents/github-copilot-reviewer.md` 
- **Scopo**: Integrazione GitHub Copilot Code Review nel workflow.
- **Benefici**: Double-validation con AI diversi per quality assurance.
- **Workflow**: `code-reviewer` → `github-copilot-reviewer` → Finalizzazione PR.

## 📚 Riferimenti Essenziali

### Documentazione Ufficiale
- **Claude Code Sub-Agents**: `https://docs.anthropic.com/en/docs/claude-code/sub-agents`
- **Tools Available**: `https://docs.anthropic.com/en/docs/claude-code/settings#tools-available-to-claude`
- **Best Practices**: `https://www.anthropic.com/engineering/claude-code-best-practices`

### Repository Analizzate e Clonate

#### 1. **Awesome Claude Prompts** 
- **URL**: `https://github.com/langgptai/awesome-claude-prompts`
- **Local Path**: `/Users/sam/awesome-claude-prompts`
- **Utilità**: Collection di 70+ categorie di prompts ottimizzati per Claude.

#### 2. **Awesome Claude Code**
- **URL**: `https://github.com/hesreallyhim/awesome-claude-code`  
- **Local Path**: `/Users/sam/awesome-claude-code`
- **Utilità**: Commands, files, workflows specifici per Claude Code.

#### 3. **Awesome AI System Prompts**
- **URL**: `https://github.com/dontriskit/awesome-ai-system-prompts`
- **Local Path**: `/Users/sam/awesome-ai-system-prompts`
- **Utilità**: System prompts per multiple AI tools incluso Claude.

#### 4. **ccundo - Checkpoint System**
- **URL**: `https://github.com/RonitSachdev/ccundo`
- **Local Path**: `/Users/sam/ccundo`
- **Utilità**: Granular undo/redo functionality per Claude Code.

#### 5. **Shrimp Task Manager**
- **URL**: Repository locale
- **Local Path**: `/Users/sam/mcp-shrimp-task-manager`
- **Utilità**: MCP server per task management avanzato.

## 🏗️ Architettura Attuale del Team

Attualmente, il sistema è composto da **28 agenti specializzati**, che collaborano per coprire un ampio spettro di compiti di sviluppo software.

## 📁 File Critici da Analizzare

### File di Configurazione Sistema
```bash
/Users/sam/.claude.json                    # Configurazione MCP servers
/Users/sam/claude-code-hooks-mastery/.claude/agents/  # Directory agenti
```

### File Template e Meta-Framework
```bash
/Users/sam/claude-code-hooks-mastery/.claude/agents/meta-agent.md
# Template per creazione nuovi agenti con:
# - Struttura YAML frontmatter
# - Guidelines tools assignment  
# - Output format standards
# - Best practices integration
```

## 🛠️ MCP Tools Disponibili

### Configurazione da `.claude.json`
```yaml
# Core MCP Servers Installati:
krag-graphiti:     # Memoria episodica persistent
krag-qdrant:       # Vector search e retrieval  
shrimp-task-manager: # Task planning avanzato
paper-search-mcp:  # Ricerca papers accademici
papers-with-code-mcp: # ML/AI papers con implementazioni
matlab-server:     # Computazione numerica MATLAB
wolframalpha:      # Calcoli matematici simbolici
youtube:           # Trascrizioni video
desktop-commander: # Automazione sistema completa
context7:          # Documentazione librerie aggiornata
git-mcp:           # GitHub integration
graphiti:          # Memory management (locale)
sequential-thinking: # Ragionamento strutturato
```

## 📋 Processo di Sviluppo Agenti

### Fase 1: Analisi Requirements
1. **Identifica gap nel team**: Usa analysis tool per role coverage
2. **Verifica tools disponibili**: Controlla `.claude.json` per capabilities
3. **Studia best practices**: Review awesome-claude repositories
4. **Analizza pattern esistenti**: Esamina agenti attuali per consistency

### Fase 2: Design e Creazione
1. **Usa meta-agent**: Genera template base con meta-agent.md
2. **Applica best practices ufficiali**:
   - Description PROACTIVELY oriented
   - Tools minimal necessary set
   - JSON output standardizzato
   - Instructions step-by-step
3. **Integra specializations**: MCP tools appropriati per dominio
4. **Test e refine**: Iterazione basata su feedback

### Fase 3: Integrazione Team
1. **Aggiorna primary-agent**: Include nuovo agente nel workflow
2. **Verifica dependencies**: Controlla interazioni con agenti esistenti
3. **Update documentation**: Mantieni questa guida aggiornata
4. **Test orchestrazione**: Verifica delegazione automatica

## 🎯 Guidelines Specifiche per Tipologie

### System/Infrastructure Agents
- **Tools necessari**: Desktop Commander suite, Bash
- **Focus**: Automazione, monitoring, deployment
- **Output**: Structured JSON con operation status
- **Memory**: KRAG-Graphiti per troubleshooting patterns

### Research/Analysis Agents  
- **Tools necessari**: Paper search, YouTube, memory tools
- **Focus**: Knowledge acquisition, literature review
- **Output**: Structured findings con relevance scores
- **Memory**: Persistent knowledge graphs

### Development Agents
- **Tools necessari**: Read, Write, Bash, Context7, Git integration
- **Focus**: Code generation, review, testing
- **Output**: Code blocks, structured feedback
- **Integration**: Gemini CLI per context esteso

### Mathematical/Computational Agents
- **Tools necessari**: WolframAlpha, MATLAB, calculation tools
- **Focus**: Numerical analysis, simulations
- **Output**: Mathematical solutions con verification
- **Visualization**: Graphs e charts quando appropriato

## 🔧 Tool Assignment Matrix

| Agent Type | Core Tools | Specialized Tools | Memory Tools |
|------------|------------|-------------------|--------------|
| **Development** | Read, Write, Bash | Context7, Git-MCP, Gemini CLI | - |
| **Research** | Read, Write | Paper-search, YouTube | KRAG-Graphiti |
| **System** | Bash | Desktop-Commander, ccundo | KRAG-Graphiti |
| **Mathematical** | Read, Write | WolframAlpha, MATLAB | - |
| **Orchestrator** | Read, Write | Shrimp-Task-Manager | KRAG-Graphiti |

## 🚀 Future Enhancement Areas

### Identificati ma Non Implementati
1. **UI/UX Designer**: Interface design, wireframing
2. **Database Architect**: Data modeling, optimization
3. **Security Specialist**: Vulnerability assessment
4. **Frontend Developer**: React/Vue/Angular specialization
5. **API Designer**: REST/GraphQL design
6. **Technical Writer**: Documentation creation
7. **Solution Architect**: High-level system design

### Potenziali Nuovi Tools
- **Design tools**: Figma, Sketch integration
- **Database tools**: SQL optimization, schema design
- **Security tools**: Vulnerability scanning
- **Performance tools**: Load testing, profiling

## 📈 Metrics e Monitoraggio

### Tracking Team Performance
- **Task completion rates** per agente
- **Delegation accuracy** del primary-agent
- **Tool utilization** patterns
- **Error recovery** effectiveness
- **Memory system** usage e efficacia

### Improvement Indicators
- **Reduced manual intervention** needs
- **Faster project completion** times
- **Higher code quality** scores
- **Better requirement** understanding
- **Improved orchestration** flow

## 🔄 Maintenance e Updates

### Quarterly Reviews
1. **Analisi performance** team
2. **Update tools** disponibili in `.claude.json`
3. **Review best practices** da community
4. **Aggiornamento documentation** e prompts
5. **Integration nuovi MCP** servers

### Continuous Improvement
- **Monitor awesome-claude** repositories per updates
- **Test nuovi prompt** patterns
- **Benchmark performance** vs baseline
- **Collect feedback** da usage patterns
- **Iterate agent designs** basato su risultati

## 📞 Support Resources

### Community e Learning
- **Claude Code GitHub Issues**: `https://github.com/anthropics/claude-code/issues`
- **Anthropic Documentation**: `https://docs.anthropic.com/en/docs/claude-code`
- **MCP Protocol**: Per sviluppo custom tools
- **Reddit Communities**: `/r/ChatGPTCoding` per discussions

### Emergency Recovery
- **ccundo**: Per rollback modifiche critiche
- **KRAG-Graphiti**: Per recovery configurazioni precedenti
- **Backup patterns**: Documenti in memory system
- **Version control**: Git per tracking changes

---

**Ultima modifica**: 2025-08-04  
**Versione Team**: 1.1 (28 agenti)  
**Prossimo review**: 2025-11-01

*Questa guida deve essere aggiornata ad ogni modifica significativa del team o integrazione di nuovi tools/repositories.*