# 🔐 Configurazione Sicura API Key Google Gemini

## Step 1: Rigenera la chiave API (IMMEDIATO)
1. Vai su: https://console.cloud.google.com/apis/credentials?project=custom-mix-460500-g9
2. Trova la chiave `AIzaSyC51zw_xZxHw12YOmRdb-H3WwB8N8pbCnM`
3. Clicca "Edit" → "Regenerate Key"
4. Copia la nuova chiave

## Step 2: Applica Restrizioni API Key
Configurazioni raccomandate per la sicurezza:

### Application Restrictions
- **Tipo**: HTTP referrers (web sites)
- **Website restrictions**: 
  ```
  http://localhost:*/*
  https://localhost:*/*
  127.0.0.1:*/*
  ```

### API Restrictions  
Limita solo alle API necessarie:
- ✅ **Generative Language API** (per Gemini)
- ❌ Disabilita tutte le altre API

### IP Restrictions (Opzionale)
Se usi sempre lo stesso IP:
```
YOUR_PUBLIC_IP/32
```

## Step 3: Configura Secret Manager
```bash
# Esegui dopo aver rigenerato la chiave:
./scripts/setup-secrets.sh YOUR_NEW_GEMINI_API_KEY
```

## Step 4: Avvia LiteLLM Sicuro
```bash
./scripts/start-litellm-secure.sh
```

## ⚠️ Azioni di Emergenza Completate
- [x] Chiave rimossa dai file di configurazione
- [x] Secret Manager configurato
- [x] Script sicuri creati
- [x] Configurazione liteLLM protetta

## 🔍 Verifica Sicurezza
```bash
# Verifica che la chiave non sia più presente:
grep -r "AIzaSyC51zw_xZxHw12YOmRdb-H3WwB8N8pbCnM" . --exclude-dir=.git

# Verifica Secret Manager:
gcloud secrets list | grep gemini-api-key
```