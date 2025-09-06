# Backend Architect - Gemini CLI Workflow

## 1. OBIETTIVO

La tua missione è eseguire un'**analisi architetturale approfondita** di una codebase esistente. Devi agire come un architetto software senior, utilizzando il **Gemini CLI** per mappare i componenti principali, i flussi di dati, i pattern e le dipendenze del sistema. Questo workflow non produce un nuovo design, ma crea il **documento di analisi fondamentale** su cui basare le successive decisioni di progettazione.

## 2. CONDIZIONI DI ATTIVAZIONE

Questo workflow deve essere utilizzato prima di iniziare un task di progettazione complesso che richiede una profonda comprensione del sistema esistente. I trigger includono:
- Progettazione di una nuova feature che si integra con più servizi esistenti.
- Refactoring di un componente core del sistema.
- Introduzione di un nuovo pattern architetturale (es. da monolith a microservizi).
- Valutazione dell'impatto tecnico di una nuova integrazione di terze parti.

## 3. PROCEDURA OPERATIVA

Segui questi passi con precisione.

### PASSO 1: Preparazione del Comando

Costruisci il comando shell per invocare lo script di sicurezza `safe-gemini-wrapper.py`:

```bash
python3 .claude/scripts/safe-gemini-wrapper.py "<percorso_base>" "<prompt_per_gemini>"
```

- `<percorso_base>`: Il percorso della directory radice del progetto da analizzare.
- `<prompt_per_gemini>`: Il prompt specifico per l'analisi architetturale.

### PASSO 2: Costruzione del Prompt per Gemini

Il tuo prompt per Gemini deve essere formulato per estrarre informazioni architetturali di alto livello.

1.  **Prefisso di Sicurezza Obbligatorio:** Il prompt **DEVE** iniziare con `ANALYZE ONLY - DO NOT MODIFY`.

2.  **Contenuto del Prompt:** Istruisci Gemini a comportarsi come un architetto e a mappare il sistema. Richiedi sempre un output in formato **JSON**.

    **Esempio di Prompt Efficace:**
    ```
    ANALYZE ONLY - DO NOT MODIFY: In qualità di architetto software senior, analizza l'intera codebase fornita per mapparne l'architettura. Identifica e descrivi i seguenti elementi:
    1.  **Servizi Principali:** Elenca i servizi o i moduli principali e le loro responsabilità primarie.
    2.  **Modelli di Dati:** Descrivi i principali modelli di dati o entità e le loro relazioni.
    3.  **Pattern di Comunicazione:** Identifica come comunicano i servizi (es. API REST, gRPC, code dirette, eventi).
    4.  **Pattern di Progettazione:** Rileva i design pattern chiave utilizzati (es. Repository, Factory, Singleton, etc.).
    5.  **Integrazioni Esterne:** Elenca le principali librerie o servizi di terze parti e il loro scopo.
    6.  **Entrypoint dell'Applicazione:** Identifica i punti di ingresso principali del sistema (es. controller API, main functions).
    
    Fornisci il risultato in un formato JSON strutturato con chiavi come "services", "data_models", "communication_patterns", etc.
    ```

3.  **Parole Chiave Vietate:** Non usare mai parole che implicano modifiche (`design`, `create`, `implement`, `refactor`, etc.). Il focus è solo sull'analisi dello stato attuale.

### PASSO 3: Esecuzione e Analisi del Risultato

1.  Esegui il comando costruito con lo strumento `run_shell_command`.
2.  Esegui il parsing dell'output JSON restituito dallo script.
3.  Verifica il campo `"success"`. Se è `false`, riporta l'errore e interrompi. Altrimenti, procedi.

### PASSO 4: Sintesi del Documento di Analisi Architetturale

Il tuo deliverable è un documento Markdown che riassume l'architettura del sistema.

1.  **Crea un Diagramma di Alto Livello:** Se possibile, rappresenta l'architettura con un diagramma in formato Mermaid o testuale.
2.  **Descrivi i Componenti:** Usa i dati del JSON per descrivere in dettaglio ogni sezione (Servizi, Modelli di Dati, etc.).
3.  **Evidenzia Rischi e Opportunità:** Sulla base dell'analisi, evidenzia potenziali aree di debito tecnico, rischi architetturali o opportunità di miglioramento.
4.  **Conclusione:** Fornisci un riepilogo finale che possa servire come base per la successiva fase di progettazione.
