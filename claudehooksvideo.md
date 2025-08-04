# Sommario dei Concetti Chiave: Claude Code Hooks

Questo documento riassume i concetti tecnici fondamentali presentati nel video "I’m HOOKED on Claude Code Hooks".

### Concetti Principali

I "Claude Code Hooks" sono un meccanismo che permette di "agganciarsi" a specifici momenti del ciclo di vita di un agente per eseguire azioni personalizzate. I due principali casi d'uso sono:

1.  **Controllo (Control)**: Intervenire *prima* che un'azione venga eseguita per bloccarla o modificarla. L'esempio classico è impedire l'esecuzione di comandi pericolosi come `rm -rf`.
2.  **Osservabilità (Observability)**: Intervenire *dopo* che un'azione è stata eseguita per registrarla (log), inviare notifiche o analizzare il comportamento dell'agente. Questo è cruciale per debuggare e migliorare i sistemi agentici.

### I 5 Hook Disponibili

Esistono cinque eventi specifici a cui ci si può agganciare:

1.  **`pre-tool-use`**: Si attiva prima che qualsiasi strumento venga eseguito. Ideale per la sicurezza e il controllo.
2.  **`post-tool-use`**: Si attiva dopo l'esecuzione di uno strumento. Fondamentale per il logging e l'osservabilità.
3.  **`notification`**: Si attiva quando Claude Code richiede un input o un permesso dall'utente.
4.  **`stop`**: Si attiva ogni volta che Claude Code completa un'intera risposta. Utile per azioni di riepilogo, come salvare l'intera cronologia della chat.
5.  **`sub-agent-stop`**: Si attiva quando un sub-agente specifico completa il suo task. Utile per notifiche granulari in flussi di lavoro paralleli.

### Configurazione e Best Practice

*   **Posizione della Configurazione**: Gli hook vengono configurati nel file `settings.json` all'interno di un blocco `"hooks"`.
*   **Struttura della Configurazione**: Per ogni evento (es. `"pre-tool-use"`), si definisce un array di "matcher" e comandi. Questo permette di eseguire script specifici (es. Python, Shell) quando un determinato strumento viene utilizzato.
*   **Isolamento della Logica**: La best practice mostrata è creare una directory dedicata (`/hooks`) nel progetto per contenere gli script che gestiscono la logica di ogni hook. Questo mantiene il codice pulito, modulare e riutilizzabile.
*   **Input degli Hook**: Ogni script di hook riceve dati strutturati (JSON) tramite standard input, contenenti informazioni contestuali sull'evento, come il nome dello strumento e i suoi parametri.

---

### Fonte Ufficiale

Per maggiori dettagli, consultare la documentazione ufficiale:
**[https://docs.anthropic.com/en/docs/claude-code/hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)**

---

## Trascrizione Tecnica Rielaborata

Di seguito, la trascrizione del video epurata dalle parti colloquiali e focalizzata sui concetti tecnici.

I Claude Code Hooks permettono di estendere le funzionalità di Claude Code. Un caso d'uso primario è la sicurezza: è possibile configurare un hook `pre-tool-use` per intercettare e bloccare comandi pericolosi come `rm -rf` prima che vengano eseguiti, proteggendo così il codebase.

Un altro caso d'uso fondamentale è l'osservabilità. Attraverso gli hook, è possibile generare log dettagliati per ogni azione eseguita da un agente. Ad esempio, usando l'hook `post-tool-use`, si possono registrare quali strumenti sono stati chiamati, con quali input e da quale agente. Questo è essenziale per scalare l'impatto degli agenti, poiché fornisce una traccia chiara delle loro azioni per il debug e l'ottimizzazione.

Gli hook disponibili sono cinque: `pre-tool-use`, `post-tool-use`, `notification`, `stop`, e `sub-agent-stop`.

L'hook `stop` si attiva al termine di ogni risposta di Claude e può essere usato per salvare l'intera cronologia della chat in un file di log. Questo è cruciale per l'analisi post-esecuzione: per migliorare un sistema agentico, è necessario poter misurare e analizzare il suo output.

La configurazione avviene nel file `settings.json`, dove si aggiunge un blocco `"hooks"`. All'interno di questo blocco, per ogni evento (es. `"post-tool-use"`), si definisce un array. Ogni elemento dell'array contiene un "matcher" (per filtrare su quali strumenti agire) e una lista di comandi da eseguire. Questi comandi sono tipicamente script esterni (Python, Shell, etc.).

Una best practice consiste nel creare una directory `hooks` nel progetto per contenere questi script, mantenendo la logica di gestione degli hook isolata e modulare. Questi script ricevono i dati dall'hook tramite standard input in formato JSON. Lo script legge questo JSON, esegue la sua logica (es. controllare se un comando è pericoloso, o scrivere un file di log) e può influenzare il flusso di esecuzione.

Ad esempio, uno script per `pre-tool-use` può analizzare l'input JSON, identificare il nome dello strumento e i suoi parametri. Se rileva un pattern pericoloso (es. `rm`), può terminare con un codice di errore e stampare un messaggio, impedendo l'esecuzione dello strumento.

Allo stesso modo, uno script per `post-tool-use` può prendere i dettagli dell'esecuzione e appenderli a un file di log, creando una cronologia completa delle attività dell'agente.

Questa capacità di programmare l'interazione e il comportamento di Claude Code lo trasforma in un "engineering primitive": un blocco di costruzione fondamentale su cui è possibile sviluppare strumenti e flussi di lavoro più complessi e robusti.