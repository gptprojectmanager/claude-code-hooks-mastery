# Riepilogo Conversazione del 02/08/2025: Piano per il Team di Agenti AI

Questo documento riassume la strategia e il piano d'azione definiti per la creazione di un team di sub-agenti di programmazione basato sul framework `claude-code-hooks-mastery`.

## 1. Obiettivo del Progetto

L'obiettivo è costruire un sistema multi-agente per automatizzare compiti di sviluppo software. Il team sarà composto da:

*   **Primary Agent (Orchestratore/CEO)**: Gestisce il flusso di lavoro e interagisce con l'utente.
*   **Planner**: Scompone task complessi in passaggi sequenziali.
*   **Coder**: Scrive il codice sorgente.
*   **Code Reviewer**: Analizza la qualità e la correttezza del codice.
*   **Tester/Debugger**: Scrive ed esegue test per validare il codice.
*   **Optimizer**: Suggerisce e applica miglioramenti al codice funzionante.
*   **Gemini Consultant**: Un agente specializzato per sfruttare la vasta finestra di contesto di Google Gemini per analisi complesse.

## 2. File e Risorse di Riferimento

La nostra strategia si basa sui seguenti file e repository:

*   **File di Contesto Iniziale**:
    *   `@/Users/sam/claude-code-hooks-mastery/multiagentsummary.md`: Fornisce il contesto concettuale sul funzionamento dei sub-agenti, basato su un transcript.
*   **Guida Tecnica Fondamentale**:
    *   `@/Users/sam/claude-code-hooks-mastery/meta-agent.md`: Il file **più importante**, che definisce la struttura JSON e le regole per la creazione di nuovi sub-agenti.
*   **Repository per Integrazione Gemini (Analizzati e Scartati)**:
    *   `https://github.com/jamubc/gemini-mcp-tool`
    *   `https://github.com/RLabs-Inc/gemini-mcp`
*   **Discussione sull'uso di Gemini CLI**:
    *   `https://www.reddit.com/r/ChatGPTCoding/comments/1lm3fxq/gemini_cli_is_awesome_but_only_when_you_make/`

## 3. Strategia di Sviluppo Adottata

Abbiamo concordato un approccio strategico preciso:

1.  **Approccio Bottom-Up**: Costruiremo prima i sub-agenti specializzati (come il `Planner`) e solo dopo istruiremo il `Primary Agent` su come orchestrarli. Questo garantisce modularità e facilità di debug.
2.  **Aderenza a `meta-agent.md`**: Ogni sub-agente sarà un file JSON che rispetta rigorosamente la struttura definita, con particolare attenzione ai campi:
    *   `description`: Istruzioni per il Primary Agent (quando e come chiamare il sub-agente).
    *   `prompt`: Istruzioni per il sub-agente stesso (cosa fare e come formattare l'output).
    *   `tools`: Limitazione degli strumenti per ogni agente secondo il principio del minimo privilegio.
3.  **Comunicazione Standardizzata**: Ogni sub-agente dovrà restituire l'output in un formato predefinito (es. JSON) specificato nel suo `prompt`, per garantire una comunicazione affidabile con il Primary Agent.

## 4. Strategia di Integrazione con Gemini CLI

Per sfruttare la finestra di contesto estesa di Gemini, abbiamo deciso di **non** utilizzare wrapper o server MCP esterni.

*   **Decisione**: Interagiremo con Gemini CLI tramite comandi shell diretti.
*   **Implementazione**: Creeremo un sub-agente dedicato, `gemini_consultant`, il cui unico scopo è eseguire il comando `gemini --prompt "{question}"` tramite lo strumento `run_shell_command` e formattare l'output. Questo approccio è stato scelto per la sua semplicità, flessibilità e bassa manutenzione.

## 5. Prossimi Passi Concordati

Il piano operativo immediato è iniziare la costruzione del team, un agente alla volta.

*   **Azione Successiva**: Creare il file di configurazione JSON per il **`Planner`**. Questo sarà il primo "specialista" del nostro team.
