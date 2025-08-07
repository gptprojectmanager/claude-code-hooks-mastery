# 🚀 Claude Monitoring Bridge - Quick Start Guide

## ✅ SISTEMA COMPLETAMENTE INTEGRATO
Il sistema Claude Monitoring Bridge è **completamente operativo** con integrazione Usage Monitor!

### 🔧 Cosa è stato implementato:
1. **Root Route aggiunta**: `localhost:8080/` ora funziona correttamente
2. **Usage Monitor CLI**: Integrato con `claude-monitor` via `uv tool install`
3. **Auto-Installation**: Script di avvio gestisce automaticamente l'installazione
4. **API completamente funzionante**: Tutti endpoints operativi con analytics

---

## 🌐 Come Utilizzare il Sistema

### **Endpoint Principali**

#### 🏠 **Root Endpoint** (NUOVO!)
```bash
curl http://localhost:8080/
```
**Risposta:**
```json
{
  "service": "Claude Monitoring Bridge",
  "version": "1.0.0", 
  "status": "running",
  "endpoints": {
    "health": "/health",
    "metrics": "/metrics",
    "alerts": "/alerts/{type}",
    "recovery": "/recovery/status"
  }
}
```

#### ❤️ **Health Check**
```bash
curl http://localhost:8080/health
```
**Cosa mostra:**
- Status sistema (healthy/degraded)
- Connessione WebSocket
- Stato recovery
- Numero alert attivi

#### 📊 **Metrics**
```bash
curl http://localhost:8080/metrics
```
**Cosa mostra:**
- Dati real-time dal sistema hooks
- Analytics sessioni Claude Code
- Stato recovery
- Alert attivi

#### 🚨 **Manual Alert Test**
```bash
curl -X POST http://localhost:8080/alerts/test
```
**Cosa fa:**
- Triggera alert manuale per testing
- Attiva recovery strategies se configurate

#### 🔄 **Recovery Status**
```bash
curl http://localhost:8080/recovery/status
```
**Cosa mostra:**
- Stato recovery corrente (normal/paused/recovering)
- Alert attivi e timestamp
- Status recovery automatico

---

## 🎯 Come Interpretare le Metriche

### **Health Response**
```json
{
  "status": "healthy",           // healthy = tutto OK, degraded = problemi
  "websocket": "connected",      // connected = hooks system attivo
  "recovery_state": "normal",    // normal/paused/recovering/failed  
  "alerts_count": 0              // numero alert attivi
}
```

### **Metrics Response**
```json
{
  "hooks_data": {                // Dati real-time hooks system
    "session_id": "xxx",
    "tool_usage_count": 45,
    "event_count": 100,
    "quality_score": 100
  },
  "usage_data": {},              // Analytics Usage Monitor (se configurato)
  "recovery_state": "normal",    // Stato recovery
  "active_alerts": {}            // Alert attualmente attivi
}
```

---

## 🔥 Funzionalità Rate Limit Recovery

### **Recovery Automatico**
Il sistema monitora e gestisce automaticamente:

1. **Rate Limits**: Exponential backoff automatico
2. **Time Limits**: Session pause/resume intelligente  
3. **Cost Limits**: Graceful degradation
4. **Token Limits**: Alert proattivi

### **Come Funziona**
- 🔍 **Monitoraggio**: Via WebSocket da hooks system
- ⚡ **Trigger**: Alert automatici su soglie configurabili
- 🛡️ **Recovery**: Strategie automatiche senza interruzioni
- 📊 **Tracking**: Tutto logged e tracciato via API

---

## 🛠️ Troubleshooting

### **Se Bridge non risponde:**
```bash
# Verifica se è attivo
curl http://localhost:8080/health

# Se non risponde, riavvia
./start.sh

# Check logs
tail -f bridge.log
```

### **Se WebSocket disconnesso:**
```bash
# Verifica Bun server hooks system attivo
curl http://localhost:4000/health

# Se necessario, avvia hooks system
cd ../apps/server && bun run dev
```

### **Per test completo sistema:**
```bash
./check_system.sh
```

---

## 📝 Comandi Rapidi

```bash
# Start bridge
./start.sh

# Check status completo
./check_system.sh

# Test tutti endpoint
curl http://localhost:8080/         # Root info
curl http://localhost:8080/health   # System health  
curl http://localhost:8080/metrics  # Full metrics
curl -X POST http://localhost:8080/alerts/test  # Manual alert
curl http://localhost:8080/recovery/status      # Recovery status
```

---

## 🎉 Sistema Completamente Operativo con Usage Monitor

✅ **API**: Tutti endpoints funzionanti  
✅ **WebSocket**: Connesso al sistema hooks  
✅ **Recovery**: Strategie automatiche attive  
✅ **Usage Monitor**: Integrato con `claude-monitor` CLI via uv  
✅ **Auto-Setup**: Installazione automatica di dipendenze  
✅ **Analytics**: Metriche avanzate e monitoring token usage  
✅ **UX**: Sistema completo senza errori!

## 🔧 Installazione Usage Monitor

Il sistema ora gestisce automaticamente l'installazione di `claude-monitor`:

### ⚡ Installazione Automatica
```bash
# Lo script start.sh installa automaticamente tutto
./start.sh
```

### 📋 Installazione Manuale (opzionale)
```bash
# Installa uv (se non presente)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Installa claude-monitor con uv (raccomandato)
uv tool install claude-monitor

# Verifica installazione
claude-monitor --help
```

### 🧪 Test Integrazione
```bash
# Verifica tutto il sistema
./check_system.sh

# Test CLI diretto
claude-monitor --view session
```

Il tuo Claude Monitoring Bridge è pronto per gestire automaticamente rate limits con analytics avanzate Usage Monitor! 🚀