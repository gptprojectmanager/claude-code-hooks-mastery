# Claude Code Hooks Mastery: Un Framework Multi-Agente Avanzato

Questo repository è un framework avanzato per l'orchestrazione di un team di sub-agenti AI specializzati, costruito su **Anthropic Claude Code**. Sfrutta i **Claude Code Hooks** per un controllo deterministico e un'osservabilità profonda, e integra il **Gemini CLI** in modo sicuro per analisi su larga scala.

<img src="images/hooked.png" alt="Claude Code Hooks" style="max-width: 800px; width: 100%;" />

## ✨ Funzionalità Principali

-   **Team di Oltre 50 Agenti Specializzati**: Un ecosistema di agenti esperti, ciascuno con un dominio di competenza specifico (es. architettura backend, sicurezza, analisi dati, linguaggi di programmazione), organizzati in una struttura a categorie chiara e manutenibile.

-   **Orchestrazione Intelligente**: Un `primary-agent` agisce come un "Intelligence Router", analizzando i task, classificandone la scala e la complessità, e delegando il lavoro all'agente più appropriato con il workflow corretto.

-   **Integrazione Sicura con Gemini CLI**: Un wrapper Python personalizzato (`safe-gemini-wrapper.py`) permette agli agenti di sfruttare la potenza di Gemini CLI per analisi su intere codebase in modalità "sola lettura" garantita, con controlli di sicurezza a più livelli (validazione prompt, hashing file, rollback Git).

-   **Workflow Dinamici e Condizionali**: Gli agenti più avanzati sono dotati di una logica decisionale interna che permette loro di scegliere dinamicamente tra un workflow standard per task semplici e un workflow potenziato con Gemini per analisi complesse e su larga scala.

-   **Dashboard di Osservabilità in Tempo Reale**: Un'applicazione web (Vue.js + Bun.js) che visualizza le interazioni tra agenti, l'uso degli strumenti e gli eventi del sistema in tempo reale.

-   **Architettura Basata su Prompt Modulari**: I workflow complessi sono definiti in file di prompt specializzati e riutilizzabili, mantenendo pulite e focalizzate le definizioni degli agenti.

## 🏛️ Architettura e Struttura del Progetto

Il cuore del sistema risiede nella directory `.claude`. La sua struttura è progettata per la massima modularità e chiarezza.

```
.
├── .claude/
│   ├── agents/
│   │   ├── backend-architecture/
│   │   ├── business-marketing/
│   │   ├── crypto/
│   │   ├── data-ai/
│   │   ├── development-architecture/
│   │   ├── infrastructure-operations/
│   │   ├── language-specialists/
│   │   ├── quality-security/
│   │   └── specialized-domains/
│   ├── commands/
│   │   └── agent_prompts/  # Prompt specializzati e riutilizzabili
│   ├── docs/               # Documentazione strategica (es. pattern di orchestrazione)
│   ├── hooks/              # Script per gli 8 eventi del ciclo di vita di Claude
│   ├── scripts/            # Script di supporto (es. safe-gemini-wrapper.py)
│   └── agents_legacy/      # Archivio di agenti e prompt obsoleti
├── apps/
│   ├── client/             # Frontend Vue.js per la dashboard di osservabilità
│   └── server/             # Backend Bun.js (API e WebSocket)
└── README.md               # Questo file
```

### Pattern Architetturali degli Agenti

Gli agenti in questo framework utilizzano tre pattern principali:

1.  **Prompt Incorporato**: L'agente è autonomo e contiene tutte le sue istruzioni nel suo file `.md`. Ideale per specialisti con un compito ben definito (es. `business-analyst`).
2.  **Caricamento Statico**: L'agente funge da "puntatore" che carica sempre un set di istruzioni da un file di prompt esterno. Utile per standardizzare agenti simili (es. tutti i `language-specialists`).
3.  **Caricamento Dinamico e Condizionale**: Il pattern più avanzato. L'agente contiene una logica decisionale interna ("Intelligence Router") che gli permette di scegliere se eseguire un workflow standard o caricare istruzioni da un prompt specializzato per compiti complessi (es. `code-reviewer` quando deve usare Gemini).

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
*Questo documento è stato aggiornato il: 2025-08-05 per riflettere la nuova architettura multi-agente.*
