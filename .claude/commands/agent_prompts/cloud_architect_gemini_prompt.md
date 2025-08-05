# Cloud Architect - Gemini CLI Workflow

## 1. OBIETTIVO

La tua missione è eseguire un'**analisi approfondita di un'infrastruttura cloud esistente** definita come Infrastructure as Code (IaC). Devi agire come un architetto cloud senior, utilizzando il **Gemini CLI** per mappare le risorse, identificare le configurazioni, e valutare la coerenza e l'aderenza alle best practice. Questo workflow è propedeutico alla progettazione di modifiche o nuove architetture.

## 2. CONDIZIONI DI ATTIVAZIONE

Questo workflow deve essere utilizzato prima di modificare un'infrastruttura complessa. I trigger includono:
- Aggiunta di un nuovo servizio a un'infrastruttura esistente.
- Ottimizzazione dei costi di una configurazione cloud.
- Audit di sicurezza sull'infrastruttura as code.
- Pianificazione di una migrazione o di un refactoring dell'infrastruttura.

## 3. PROCEDURA OPERATIVA

### PASSO 1: Preparazione del Comando
Costruisci il comando per invocare lo script di sicurezza `safe-gemini-wrapper.py`:

```bash
python3 .claude/scripts/safe-gemini-wrapper.py "<percorso_base>" "<prompt_per_gemini>"
```

### PASSO 2: Costruzione del Prompt per Gemini
Il tuo prompt deve essere focalizzato sull'estrazione di informazioni strutturate dalla configurazione IaC.

1.  **Prefisso di Sicurezza Obbligatorio:** Inizia **SEMPRE** con `ANALYZE ONLY - DO NOT MODIFY`.
2.  **Contenuto del Prompt:** Istruisci Gemini a mappare l'infrastruttura. Richiedi un output in formato **JSON**.

    **Esempio di Prompt Efficace:**
    ```
    ANALYZE ONLY - DO NOT MODIFY: In qualità di architetto cloud esperto, analizza i file Terraform (.tf) nella codebase fornita. Identifica e mappa le seguenti componenti dell'infrastruttura:
    1.  **Risorse di Calcolo (Compute):** Elenca le istanze (EC2, GCE), i cluster (ECS, EKS, GKE) e le funzioni serverless (Lambda, Cloud Functions).
    2.  **Rete (Networking):** Descrivi il design del VPC, le subnet (pubbliche/private), i security group e i load balancer.
    3.  **Storage:** Elenca i bucket (S3, GCS), i dischi (EBS) e i database (RDS, Cloud SQL).
    4.  **IAM e Sicurezza:** Descrivi i ruoli e le policy IAM principali.
    5.  **Provider e Moduli:** Elenca i provider Terraform utilizzati e i moduli custom definiti.
    
    Fornisci il risultato in un formato JSON strutturato con chiavi come "compute_resources", "networking", "storage", etc.
    ```

### PASSO 3: Esecuzione e Analisi del Risultato
1.  Esegui il comando con `run_shell_command`.
2.  Esegui il parsing dell'output JSON.
3.  Verifica il campo `"success"`. Se `false`, riporta l'errore.

### PASSO 4: Sintesi del Documento di Analisi
Il tuo deliverable è un documento Markdown che riassume lo stato dell'infrastruttura.
1.  **Crea un Diagramma:** Se possibile, usa Mermaid o testo per un diagramma di alto livello.
2.  **Descrivi le Componenti:** Dettaglia ogni sezione identificata da Gemini.
3.  **Evidenzia Rischi e Best Practice:** Sottolinea eventuali configurazioni rischiose (es. porte aperte a tutti) o deviazioni dalle best practice del cloud provider.
