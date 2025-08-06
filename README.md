# Claude Code Hooks Mastery: KRAG Semantic Hub-and-Spoke Framework

Questo repository implementa un **sistema multi-agente semantico avanzato** che risolve i problemi fondamentali di coordinamento identificati nella ricerca di [claude-code-sub-agent-collective](https://github.com/vanzan01/claude-code-sub-agent-collective): **Context Degradation**, **Coordination Drift**, e **Quality Inconsistency**.

Il nostro approccio utilizza **KRAG (Knowledge Retrieval Augmented Generation) Memory** per superare i limiti dei sistemi file-based, offrendo **semantic intelligence**, **vector similarity**, **graph relationships** e **JIT context loading**.

<img src="images/hooked.png" alt="Claude Code Hooks" style="max-width: 800px; width: 100%;" />

## 🧠 Breakthrough Tecnologici

### **KRAG Semantic Hub-and-Spoke Architecture**
Risolve i **3 problemi critici** dei sistemi multi-agente tradizionali:

**🔥 Context Degradation → KRAG Vector Similarity**
- **Problema**: Agenti perdono context tra interazioni  
- **Soluzione**: Memory semantica con vector embeddings e automatic context expansion

**🔥 Coordination Drift → KRAG Relationship Mapping** 
- **Problema**: Comunicazione P2P inaffidabile e non-deterministica
- **Soluzione**: Graph relationships con Hub-and-Spoke coordination tramite primary agent

**🔥 Quality Inconsistency → KRAG Quality Gates**
- **Problema**: Agenti saltano steps senza enforcement
- **Soluzione**: Graph-based quality gates con semantic validation obbligatoria

### **✨ Funzionalità Chiave**

-   🎯 **KRAG Memory Zones**: Zone di memoria isolate che prevengono race conditions
-   🔒 **HANDOFF_TOKEN Semantici**: Token con vector embeddings per validation context
-   ⚡ **JIT Context Loading**: Assembly semantico di context minimale e rilevante  
-   🛡️ **Quality Gates Graph-Based**: 6 gate obbligatori (Planning→Infrastructure→Implementation→Testing→Polish→Completion)
-   🔄 **Progressive Retry Logic**: 3 tentativi con escalation automatica
-   📊 **Semantic Agent Routing**: Selezione agenti basata su compatibility semantica
-   💾 **Knowledge Graph Persistence**: Apprendimento incrementale tramite graph accumulation
-   🎮 **Real-Time Observability**: Dashboard Vue.js per monitoring coordinamento agenti
-   🚨 **Claude Monitoring Bridge**: Sistema automatico di prevenzione rate limits e recovery seamless

## 🏗️ KRAG Memory Architecture

### **Memory Zone Isolation (Anti-Race Conditions)**
```
KRAG Group IDs:
├── session_{timestamp}_primary     # Primary agent coordination memory
├── session_{timestamp}_dev         # Development agents working memory  
├── session_{timestamp}_security     # Security agents working memory
├── session_{timestamp}_research     # Research cache (shared read-only)
├── validated_knowledge             # Long-term knowledge (shared read-only)
└── system_coordination            # HANDOFF_TOKENs, Quality Gates
```

**Access Control:**
- **Primary Agent**: Full R/W access to ALL zones (Memory Mediator)
- **Sub-agents**: R/W own zone + Read access to shared zones only
- **NO cross-zone writes** by sub-agents (eliminates memory conflicts)

### **HANDOFF_TOKEN Semantic Validation**
```yaml
Entity: handoff_token_COMPLEX_PM9N5
Properties:
  - token_id: "COMPLEX_PM9N5"
  - source_agent: "primary-agent"
  - target_agent: "backend-architect"
  - context_vector: [semantic embedding]
  - validation_status: "pending/validated/failed"
  - retry_count: 0/3
  - expires_at: timestamp + 30min

Relationships:
  - requires → [context_entities]
  - validates → quality_gate_entity
  - depends_on → prerequisite_tokens
```

### **Quality Gates Graph Dependencies**
```yaml
planning_gate → blocks → infrastructure_gate
infrastructure_gate → blocks → implementation_gate  
implementation_gate → blocks → testing_gate
testing_gate → blocks → polish_gate
polish_gate → blocks → completion_gate
```

## 🏛️ Project Structure

```
.
├── .claude/
│   ├── agents/                    # 50+ Specialized agents organized by domain
│   │   ├── development-architecture/  # Primary agent + core development
│   │   ├── language-specialists/     # Python, JS, TS, Rust, Go, etc.
│   │   ├── infrastructure-operations/ # Cloud, DevOps, Database
│   │   ├── quality-security/          # Security, Testing, Code Review
│   │   ├── data-ai/                   # ML, Data Engineering, AI
│   │   ├── business-marketing/        # Content, Sales, Legal
│   │   └── specialized-domains/       # Crypto, Finance, Research
│   ├── commands/agent_prompts/    # Detailed agent prompts with KRAG integration
│   ├── hooks/                     # Claude Code lifecycle hooks
│   └── settings.json             # MCP servers: KRAG, Shrimp, Context7
├── apps/
│   ├── client/                   # Vue.js observability dashboard
│   └── server/                   # Bun.js backend + WebSocket
├── claude-monitoring-bridge/      # 🚨 NEW: Automatic rate limit prevention system
│   ├── bridge.py                 # Core monitoring bridge component
│   ├── config.yaml              # Alert thresholds and recovery strategies
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Complete setup and usage guide
└── README.md
```

## 🚀 Usage & Quick Start

### **MCP Server Dependencies**
```bash
# KRAG Memory servers (required)
# localhost:8000 - krag-graphiti-memory
# localhost:8001 - krag-qdrant-memory

# Task Management
npm install -g mcp-shrimp-task-manager

# Context Research  
npm install -g @upstash/context7-mcp
```

### **Primary Agent Usage**
```bash
# Hub-and-Spoke coordination via primary agent
@primary-agent-sonnet "implement user authentication system with security audit"

# Automatic flow:
# 1. KRAG semantic analysis of request
# 2. JIT context loading from knowledge graph  
# 3. Quality gate initialization (6 gates)
# 4. HANDOFF_TOKEN creation with semantic validation
# 5. Agent routing based on vector similarity
# 6. Progressive retry logic with escalation
# 7. Knowledge persistence in validated_knowledge zone
```

### **System Architecture Patterns**

**1. 🧠 KRAG Semantic Memory Pattern**
- **Memory zones** isolate per prevenire race conditions
- **Vector similarity** per context discovery automatico  
- **Graph relationships** per dependency enforcement
- **JIT context assembly** per handoff efficenti

**2. 🔒 HANDOFF_TOKEN Validation Pattern**
- **Semantic tokens** con context vectors embedded
- **Progressive retry logic** (max 3 attempts)  
- **Automatic expiry** (30min) per prevenire stale handoffs
- **Cryptographic validation** tramite KRAG graph entities

**3. 🛡️ Quality Gate Enforcement Pattern**  
- **6 mandatory gates**: Planning → Infrastructure → Implementation → Testing → Polish → Completion
- **Graph-based dependencies** (NO bypass possible)
- **Semantic validation** tramite vector similarity su criteria
- **Failure tracking** con remediation requirements specifici

## 🔬 Research Foundation

Questo sistema è basato sulla ricerca di [claude-code-sub-agent-collective](https://github.com/vanzan01/claude-code-sub-agent-collective) che identifica i **3 problemi fondamentali** dei sistemi multi-agente:

- **Context Degradation** - Agenti perdono context tra interazioni
- **Coordination Drift** - Comunicazione P2P diventa inaffidabile  
- **Quality Inconsistency** - Agenti saltano steps senza enforcement

**Il nostro KRAG approach supera i limiti file-based** offrendo:
- ✅ **Semantic intelligence** vs keyword matching  
- ✅ **Vector similarity** vs manual file organization
- ✅ **Graph relationships** vs isolated files
- ✅ **Automatic discovery** vs manual search
- ✅ **Real-time updates** vs static cache invalidation

## 🚀 Come Funziona

1.  L'utente fornisce una richiesta al `primary-agent`.
2.  Il `primary-agent` analizza e classifica il task.
3.  Utilizzando il suo "Intelligence Router", seleziona l'agente specializzato più adatto e decide quale workflow (standard o avanzato) deve utilizzare.
4.  L'agente specializzato esegue il task, se necessario utilizzando il `safe-gemini-wrapper.py` per analisi su larga scala.
5.  Il risultato viene passato a un agente validatore (es. `work-validator`), che può anch'esso utilizzare un workflow Gemini per una validazione contestuale.
6.  Il `primary-agent` supervisiona il processo e riporta il risultato finale all'utente.

## 🛠️ Stack Tecnologico

-   **Core AI**: Anthropic Claude Code
-   **Orchestrazione e Analisi**: Gemini CLI, Python
-   **Frontend Osservabilità**: Vue.js 3, TypeScript
-   **Backend Osservabilità**: Bun.js, ElysiaJS, WebSockets
-   **CI/CD**: GitHub Actions

## 🚀 Quick Start

### Prerequisiti
- [Claude Code CLI](https://claude.ai/code) installato
- [Gemini CLI](https://ai.google.dev/gemini-api) configurato (opzionale per analisi avanzate)
- Node.js/Bun per la dashboard di osservabilità

### Installazione
```bash
# Clone del repository
git clone https://github.com/your-username/claude-code-hooks-mastery.git
cd claude-code-hooks-mastery

# Setup dashboard (opzionale)
cd apps/server && bun install
cd ../client && npm install
```

### Primo Utilizzo
```bash
# Avvia Claude Code nella directory del progetto
claude-code

# Esempio di utilizzo del primary-agent
"Aiutami a ottimizzare questa API REST per gestire 10k richieste/sec"
```

## 🤖 Agenti Disponibili

### 📊 Panoramica (55+ Agenti Specializzati)

| Categoria | Agenti | Descrizione |
|-----------|---------|-------------|
| **Language Specialists** | 9 agenti | TypeScript, Rust, Go, C/C++, Java, PHP, Python, iOS, SQL |
| **Backend Architecture** | 3 agenti | Backend design, Database architecture, Cloud architecture |
| **Infrastructure Operations** | 6 agenti | DevOps, System admin, Data engineering, AI engineering |
| **Quality & Security** | 7 agenti | Code review, Security auditing, Testing, Validation |
| **Business & Marketing** | 8 agenti | API docs, Business analysis, Content marketing, Legal |
| **Specialized Domains** | 4 agenti | Research, Mathematics, Meta-agent creation, LLM research |
| **Crypto Analytics** | 12 agenti | Market analysis, Investment strategies, Correlation tracking |
| **Data & AI** | 2 agenti | AI engineering, Data pipeline development |

### 🎯 Agenti Chiave

- **`primary-agent-sonnet`**: Orchestratore intelligente e router principale
- **`code-reviewer-sonnet`**: Code review con analisi Gemini su larga scala
- **`security-auditor-opus`**: Audit di sicurezza completo
- **`backend-architect-sonnet`**: Design di architetture backend scalabili
- **`work-validator-sonnet`**: Validazione finale dei deliverable

## 📊 Dashboard di Osservabilità

La dashboard fornisce insights in tempo reale su:
- **Flusso degli Agenti**: Visualizzazione delle delegazioni tra agenti
- **Utilizzo degli Strumenti**: Monitoraggio delle chiamate API e tool usage
- **Performance Metrics**: Tempi di risposta e throughput
- **Event Timeline**: Cronologia completa delle operazioni

```bash
# Avvio della dashboard
cd apps/server && bun run dev    # Server API su porta 3000
cd apps/client && npm run dev    # Frontend su porta 5173
# Accedi a http://localhost:5173
```

## 🚨 Claude Monitoring Bridge - NEW!

Il **Claude Monitoring Bridge** è un sistema automatico di prevenzione rate limits e recovery che monitora l'utilizzo di Claude Code e previene interruzioni delle sessioni di sviluppo.

### 🎯 Problema Risolto
Durante lo sviluppo di sistemi complessi con Claude Code, è comune raggiungere rate limits che interrompono il workflow. Il bridge risolve questo problema attraverso:

- **Monitoring Proattivo**: Rileva l'avvicinamento ai limiti (token, tempo, costo)
- **Alert Automatici**: Notifiche al raggiungimento soglie configurabili  
- **Recovery Intelligente**: Strategie automatiche di recupero senza perdita di contesto
- **Dashboard Unificata**: Metriche integrate tra Usage Monitor e hooks system

### 🏗️ Architettura Bridge
```
Claude Code → Python Hooks → Bun Server :4000 → Bridge Component → Usage Monitor + Auto Recovery + Dashboard
```

**OPZIONE C - Hybrid Bridge**: Zero modifiche ai sistemi esistenti, architettura additiva.

### ⚡ Quick Start Bridge
```bash
cd claude-monitoring-bridge/

# Installa dependencies  
pip3 install -r requirements.txt

# Avvia il bridge (richiede Bun server attivo)
python3 bridge.py

# Test APIs
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

### 📊 API Endpoints Bridge
- `GET /metrics` - Metriche unificate da Usage Monitor + hooks system
- `GET /health` - Stato di salute del bridge e delle connessioni
- `POST /alerts/{type}` - Trigger manuali alert (testing)
- `GET /recovery/status` - Stato attuale delle strategie di recovery

### 🔧 Strategie di Recovery
- **Rate Limit**: Exponential backoff automatico (1s → 32s)
- **Time Limit**: Session pause con resume automatico
- **Cost Limit**: Graceful degradation della funzionalità
- **Token Limit**: Alert proattivi all'80% di utilizzo

### 🎯 Meta-Achievement
Il bridge ha dimostrato la sua utilità durante il proprio sviluppo: abbiamo raggiunto il rate limit di Claude AI mentre implementavamo il sistema che previene esattamente questo problema! Perfect use case validation.

**Documentazione Completa**: `claude-monitoring-bridge/README.md`

## 🔒 Sicurezza

Il framework implementa diversi livelli di sicurezza:
- **Safe Gemini Wrapper**: Analisi in sola lettura con controlli di integrità
- **Prompt Validation**: Sanitizzazione automatica degli input
- **Git Rollback**: Capacità di ripristino automatico in caso di modifiche indesiderate
- **Audit Trail**: Log completo di tutte le operazioni degli agenti

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/amazing-agent`)
3. Commit delle modifiche (`git commit -m 'Add amazing new agent'`)
4. Push al branch (`git push origin feature/amazing-agent`)
5. Apri una Pull Request

### Aggiungere Nuovi Agenti
Consulta la [Guida alla Creazione di Agenti](.claude/docs/agent-creation-guide.md) per le best practices.

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 🙏 Riconoscimenti

- **Anthropic** per Claude Code e l'ecosistema di tool
- **Google** per Gemini CLI e le API
- La community open source per gli strumenti e le librerie utilizzate

---
*Questo documento è stato aggiornato il: 2025-08-06 per includere il Claude Monitoring Bridge e la nuova architettura multi-agente.*
