# 🧠 Team Development Guide - Claude Code Multi-Agent System

## 📋 Panoramica

Questa guida completa documenta il processo di sviluppo, miglioramento e creazione di nuovi agenti per il sistema multi-agente Claude Code. Contiene tutti i riferimenti, repository, file e best practices necessari per future iterazioni del team.

## 🎯 Obiettivo del Sistema

Costruire un team di sub-agenti specializzati per automatizzare compiti di sviluppo software professionale, con orchestrazione intelligente, memoria persistente e capabilities enterprise-level.

## 🆕 **Aggiornamenti Recenti di Sicurezza**

### Agente Cleanup-Validator Implementato
- **File**: `.claude/agents/cleanup-validator.md`
- **Scopo**: Prevenzione loop infiniti e gestione igiene workflow
- **Tools**: Cleanup completo task e memoria con safety protocols

### Limitazioni Permessi Bash Implementate
- **File**: `.claude/settings.local.json`
- **Modifiche**: 
  - `"Bash(rm:*)"` → Pattern specifici sicuri
  - `"Bash(chmod:*)"` → Solo permessi standard (644, 755, +x)
- **Sicurezza**: Prevenzione comandi distruttivi mantenendo funzionalità

### Primary Agent Potenziato  
- **Nuovi Tools**: `delete_task`, `verify_task` per cleanup immediato
- **Efficienza**: Controllo diretto task senza overhead delegation

### Sistema Dual-Review GitHub Copilot Implementato
- **File**: `.claude/agents/github-copilot-reviewer.md` 
- **Scopo**: Integrazione GitHub Copilot Code Review nel workflow
- **Benefici**: Double-validation con AI diversi per quality assurance
- **Workflow**: code-reviewer → github-copilot-reviewer → PR finalization

## 📚 Riferimenti Essenziali

### Documentazione Ufficiale
- **Claude Code Sub-Agents**: `https://docs.anthropic.com/en/docs/claude-code/sub-agents`
- **Tools Available**: `https://docs.anthropic.com/en/docs/claude-code/settings#tools-available-to-claude`
- **Best Practices**: `https://www.anthropic.com/engineering/claude-code-best-practices`

### Repository Analizzate e Clonate

#### 1. **Awesome Claude Prompts** 
- **URL**: `https://github.com/langgptai/awesome-claude-prompts`
- **Local Path**: `/Users/sam/awesome-claude-prompts`
- **Utilità**: Collection di 70+ categorie di prompts ottimizzati per Claude
- **Focus**: Development workflows, business applications, creative tasks

#### 2. **Awesome Claude Code**
- **URL**: `https://github.com/hesreallyhim/awesome-claude-code`  
- **Local Path**: `/Users/sam/awesome-claude-code`
- **Utilità**: Commands, files, workflows specifici per Claude Code
- **Focus**: Agentic coding patterns e best practices

#### 3. **Awesome AI System Prompts**
- **URL**: `https://github.com/dontriskit/awesome-ai-system-prompts`
- **Local Path**: `/Users/sam/awesome-ai-system-prompts`
- **Utilità**: System prompts per multiple AI tools incluso Claude
- **Focus**: AI agent builders e prompt engineers

#### 4. **ccundo - Checkpoint System**
- **URL**: `https://github.com/RonitSachdev/ccundo`
- **Local Path**: `/Users/sam/ccundo`
- **Utilità**: Granular undo/redo functionality per Claude Code
- **Installato**: `npm install -g ccundo`
- **Features**: Zero-config, cascading safety, detailed previews

#### 5. **Shrimp Task Manager**
- **URL**: Repository locale
- **Local Path**: `/Users/sam/mcp-shrimp-task-manager`
- **Utilità**: MCP server per task management avanzato
- **Configurato**: In `.claude.json` come MCP server

## 🏗️ Architettura Attuale del Team

### Core Development Team (5 agenti)
1. **planner**: Planning con Shrimp Task Manager
2. **coder**: Sviluppo con Gemini CLI + Context7
3. **code-reviewer**: Review con GitHub search + security
4. **tester-debugger**: Testing completo
5. **optimizer**: Ottimizzazione con documentazione

### Domain Specialists (3 agenti)
6. **researcher**: Ricerca accademica + YouTube + memoria
7. **mathematician**: WolframAlpha + MATLAB + computazione
8. **system-admin**: DevOps + Desktop Commander + ccundo

### Orchestrator (1 agente)
9. **primary-agent**: Project management + memoria + coordinamento

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

### File di Documentazione Strategica
```bash
/Users/sam/claude-code-hooks-mastery/summaryconversation0208.md
# Piano strategico originale con:
# - Approccio bottom-up
# - Framework conceptuale
# - Strategia Gemini CLI

/Users/sam/claude-code-hooks-mastery/multiagentsummary.md  
# Best practices teoriche da transcript video:
# - Information flow sub-agents
# - System vs user prompts
# - Isolation patterns
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

**Ultima modifica**: 2025-01-02  
**Versione Team**: 1.0 (9 agenti)  
**Prossimo review**: 2025-04-01

*Questa guida deve essere aggiornata ad ogni modifica significativa del team o integrazione di nuovi tools/repositories.*