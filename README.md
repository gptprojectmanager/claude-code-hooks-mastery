# Claude Code Hooks Mastery + Multi-Agent System

Questo repository è un sistema avanzato che dimostra l'uso dei **Claude Code Hooks** per un controllo deterministico sul comportamento dell'AI, potenziato da un **sistema multi-agente** e una **dashboard di osservabilità** in tempo reale.

<img src="images/hooked.png" alt="Claude Code Hooks" style="max-width: 800px; width: 100%;" />

## ✨ Funzionalità Principali

- **Sistema Multi-Agente Completo**: Un team di agenti specializzati (attualmente 28) che collaborano per automatizzare workflow di sviluppo complessi.
- **Dashboard di Osservabilità in Tempo Reale**: Un'applicazione web (Vue.js + Bun.js) che visualizza le interazioni tra agenti, l'uso degli strumenti e gli eventi del sistema in tempo reale tramite WebSockets.
- **Workflow di Revisione Duale Automatizzato**: Un processo di revisione del codice che sfrutta un agente interno e l'integrazione con **GitHub Copilot** per una quality assurance completa, orchestrato tramite GitHub Actions.
- **Sicurezza e Controllo**: Hook di sicurezza che prevengono l'esecuzione di comandi pericolosi e un wrapper personalizzato per l'uso "sola lettura" di Gemini CLI.
- **Architettura Basata su UV**: I singoli script dei ganci utilizzano `uv` per gestire le dipendenze in modo isolato e portabile.

## 🛠️ Stack Tecnologico

- **Core AI**: Anthropic Claude Code
- **Orchestrazione**: Gemini CLI
- **Frontend Osservabilità**: Vue.js 3, TypeScript, Tailwind CSS
- **Backend Osservabilità**: Bun.js, ElysiaJS, WebSockets
- **Database**: SQLite per la persistenza degli eventi
- **CI/CD & Automazione**: GitHub Actions, GitHub CLI

## 🚀 Guida Rapida (Getting Started)

### Prerequisiti
- **[Astral UV](https://docs.astral.sh/uv/getting-started/installation/)**: Per l'esecuzione degli script dei ganci.
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)**: L'interfaccia CLI di Anthropic.
- **[Bun.js](https://bun.sh/docs/installation)**: Per eseguire il server di osservabilità.
- **[GitHub CLI](https://cli.github.com/)**: Per l'integrazione con GitHub.

### Avvio del Sistema Completo
Il modo più semplice per avviare sia il server di osservabilità che il client è usare lo script fornito.

```bash
# Esegui questo comando dalla root del repository
./scripts/start-system.sh
```
Questo script si occuperà di installare le dipendenze e avviare entrambi i server. Una volta avviato, la dashboard di osservabilità sarà accessibile all'indirizzo `http://localhost:5173`.

## 🏛️ Struttura del Progetto

```
.
├── .claude/
│   ├── agents/         # Definizioni dei 28+ agenti specializzati
│   ├── commands/       # Istruzioni per gli agenti (es. come usare Gemini in sicurezza)
│   ├── docs/           # Documentazione strategica interna
│   └── hooks/          # Script Python (uv) per gli 8 eventi del ciclo di vita di Claude
├── .github/
│   └── workflows/      # Workflow di GitHub Actions per la revisione automatica con Copilot
├── apps/
│   ├── client/         # Codice sorgente del frontend Vue.js per la dashboard
│   └── server/         # Codice sorgente del backend Bun.js (API e WebSocket)
├── scripts/
│   └── start-system.sh # Script per avviare l'intero sistema di osservabilità
└── README.md           # Questo file
```

## 🔄 Cronologia Recente delle Modifiche (Changelog)

- **feat(ui)**: Migliorata la gestione degli errori per la funzionalità di copia negli appunti, come suggerito da Copilot.
- **fix(workflow)**: Risolti molteplici problemi nel workflow di GitHub Actions, inclusa la gestione dei label, il contesto di esecuzione e l'installazione della CLI di GitHub.
- **docs**: Aggiornata la documentazione interna (`team-development-guide.md`, `gemini-cli-orchestration-patterns.md`) per riflettere lo stato attuale del progetto e le architetture di sicurezza.
- **feat(git)**: Eseguito il merge dal repository upstream e risolti i conflitti per mantenere la codebase aggiornata.
- **docs(agent)**: Corretto e allineato il prompt dell'agente `github-copilot-reviewer` per renderlo coerente con il workflow funzionante.

---
*Questo documento è stato aggiornato il: 2025-08-04*