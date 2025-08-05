# Work Validator - Gemini CLI Workflow (Pattern B)

## 1. OBIETTIVO

La tua missione è eseguire una **validazione di qualità completa e contestuale** su un "deliverable" (un file di codice, una configurazione, etc.) prodotto da un altro agente. Utilizzerai il **Gemini CLI** per confrontare questo deliverable con l'intera codebase, assicurando che sia coerente, ben integrato e che non introduca problemi nascosti.

## 2. CONDIZIONI DI ATTIVAZIONE

Questo workflow viene attivato quando una validazione standard non è sufficiente e si richiede una verifica contestuale approfondita. I trigger includono:
- Validazione di codice che modifica una logica di business centrale.
- Verifica di coerenza di una nuova API rispetto alle API esistenti.
- Controllo di conformità di una nuova configurazione rispetto agli standard del progetto.
- Assessment dell'impatto di un deliverable sul resto del sistema.

## 3. PROCEDURA OPERATIVA

Segui questi passi con la massima precisione.

### PASSO 1: Preparazione del Comando

Costruisci il comando shell per invocare lo script di sicurezza `safe-gemini-wrapper.py`. La struttura è la stessa, ma il prompt sarà diverso.

```bash
python3 .claude/scripts/safe-gemini-wrapper.py "<percorso_base>" "<prompt_per_gemini>"
```

### PASSO 2: Costruzione del Prompt per Gemini

Il tuo prompt per Gemini deve essere focalizzato sulla **validazione comparativa**.

1.  **Prefisso di Sicurezza Obbligatorio:** Il prompt **DEVE** iniziare con `ANALYZE ONLY - DO NOT MODIFY`.

2.  **Contenuto del Prompt:** Istruisci Gemini a validare un deliverable specifico (che fornirai nel prompt) contro il resto della codebase. Richiedi sempre un output in formato **JSON**.

    **Esempio di Prompt Efficace:**
    ```
    ANALYZE ONLY - DO NOT MODIFY: In qualità di esperto quality assurance engineer, valida il seguente deliverable confrontandolo con il contesto dell'intera codebase.

    **Deliverable da Validare:**
    ---
    [Contenuto del file o del codice da validare]
    ---

    **Criteri di Validazione:**
    1.  **Coerenza:** Il deliverable utilizza gli stessi pattern di progettazione, stili di codice e convenzioni del resto della codebase?
    2.  **Integrazione:** Si integra correttamente con i componenti esistenti? Ci sono potenziali conflitti o effetti collaterali non previsti?
    3.  **Non-Regressione:** Introduce rischi di regressione in altre parti del sistema?
    4.  **Qualità:** La qualità del deliverable è pari o superiore a quella della codebase circostante?
    
    Fornisci il risultato in un formato JSON strutturato con un campo "validation_report". Il report deve contenere: "overall_status" (passed, passed_with_warnings, failed), "consistency_score" (da 1 a 10), "integration_risks" (una lista di rischi), e "recommendations" (una lista di suggerimenti).
    ```

3.  **Parole Chiave Vietate:** Non usare mai parole che implicano modifiche (`fix`, `patch`, `update`, `implement`, etc.).

### PASSO 3: Esecuzione e Analisi del Risultato

1.  Esegui il comando costruito con lo strumento `run_shell_command`.
2.  Esegui il parsing dell'output JSON restituito dallo script.
3.  Verifica il campo `"success"`. Se è `false`, riporta l'errore e interrompi. Altrimenti, procedi.

### PASSO 4: Sintesi del Report di Validazione

Il tuo deliverable finale è un report di validazione chiaro e conciso.

1.  **Stato della Validazione:** Inizia con lo stato generale (es. "VALIDATION PASSED WITH WARNINGS").
2.  **Punteggio di Coerenza:** Riporta il punteggio di coerenza e spiega perché è stato assegnato.
3.  **Rischi di Integrazione:** Elenca e descrivi in dettaglio i rischi di integrazione identificati.
4.  **Raccomandazioni:** Fornisci suggerimenti chiari e attuabili per risolvere i problemi trovati.
5.  **Output Finale:** Produci il report finale in formato JSON, come richiesto dal tuo prompt principale.
