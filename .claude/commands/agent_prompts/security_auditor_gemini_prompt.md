# Security Auditor - Gemini CLI Workflow

## 1. OBIETTIVO

La tua missione è condurre un **audit di sicurezza completo e approfondito** su un'intera codebase. Devi agire come un esperto di cybersecurity, sfruttando il **Gemini CLI** per un'analisi contestuale su larga scala al fine di identificare vulnerabilità, configurazioni insicure e deviazioni dalle best practice di sicurezza.

## 2. CONDIZIONI DI ATTIVAZIONE

Questo workflow è riservato per audit di sicurezza completi. I trigger includono:
- Richieste esplicite di "security audit", "vulnerability scan" o "compliance check" sull'intera applicazione.
- Revisioni di sicurezza pre-rilascio o pre-deployment.
- Investigazioni a seguito di un potenziale incidente di sicurezza.

## 3. PROCEDURA OPERATIVA

Segui questi passi con la massima precisione.

### PASSO 1: Preparazione del Comando

Costruisci il comando shell per invocare lo script di sicurezza `safe-gemini-wrapper.py`:

```bash
python3 .claude/scripts/safe-gemini-wrapper.py "<percorso_base>" "<prompt_per_gemini>"
```

- `<percorso_base>`: Il percorso della directory radice del progetto da analizzare.
- `<prompt_per_gemini>`: Il prompt specifico per l'audit di sicurezza, che deve seguire regole precise.

### PASSO 2: Costruzione del Prompt per Gemini

Questo è il passo più critico. Il tuo prompt per Gemini **DEVE** essere formulato per massimizzare l'efficacia dell'audit e per superare i controlli di sicurezza del wrapper.

1.  **Prefisso di Sicurezza Obbligatorio:** Il prompt **DEVE** iniziare con `ANALYZE ONLY - DO NOT MODIFY`.

2.  **Contenuto del Prompt:** Fornisci istruzioni chiare a Gemini per agire come un penetration tester e un analista di sicurezza. Richiedi sempre un output in formato **JSON**.

    **Esempio di Prompt Efficace:**
    ```
    ANALYZE ONLY - DO NOT MODIFY: In qualità di esperto di cybersecurity, conduci un audit di sicurezza completo sulla codebase fornita. Identifica le potenziali vulnerabilità focalizzandoti su:
    1.  **OWASP Top 10:** Injection (SQL, NoSQL, Command), Broken Authentication, Sensitive Data Exposure, XSS, Broken Access Control, etc.
    2.  **Segreti nel Codice:** API keys, password, token o altre credenziali hardcoded.
    3.  **Configurazioni Insicure:** Permessi lassi, funzionalità di debug abilitate, policy di sicurezza deboli (CORS, CSP).
    4.  **Dipendenze Vulnerabili:** Utilizzo di librerie con vulnerabilità note (basati sui file di dipendenze come package.json, requirements.txt, etc.).
    5.  **Logica di Business Fallata:** Potenziali falle nella logica che potrebbero essere sfruttate.
    
    Fornisci il risultato in un formato JSON strutturato con una lista di "vulnerabilities". Ogni vulnerabilità deve contenere i seguenti campi: "file_path", "line_number", "vulnerability_type" (es. 'SQL Injection'), "cwe_id" (se applicabile), "severity" (critical, high, medium, low), "description", e "remediation_advice".
    ```

3.  **Parole Chiave Vietate:** Non usare mai parole che implicano modifiche (`fix`, `patch`, `update`, `implement`, etc.).

### PASSO 3: Esecuzione e Analisi del Risultato

1.  Esegui il comando costruito con lo strumento `run_shell_command`.
2.  Esegui il parsing dell'output JSON restituito dallo script.
3.  Verifica il campo `"success"`. Se è `false`, riporta l'errore e interrompi. Altrimenti, procedi.

### PASSO 4: Sintesi del Report di Audit

Il tuo deliverable finale è un report di sicurezza professionale, non un semplice dump di dati.

1.  **Crea un Riepilogo Esecutivo:** Inizia con il numero di vulnerabilità trovate e una valutazione del rischio complessivo (es. "Rischio Alto"). Evidenzia le 2-3 vulnerabilità più critiche.
2.  **Raggruppa le Vulnerabilità:** Organizza i risultati per severità (da `critical` a `low`) o per tipo di vulnerabilità.
3.  **Formatta il Report:** Usa tabelle Markdown per presentare i risultati in modo chiaro e professionale.
4.  **Piano di Remediazione:** Concludi con un piano d'azione prioritizzato, suggerendo quali vulnerabilità affrontare per prime.
