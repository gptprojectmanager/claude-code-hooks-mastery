# Claude Monitoring Bridge

**OPZIONE C - Hybrid Bridge Implementation**

Integrazione semplice per monitoring e recovery automatico rate/time limits Claude Code.
Bridge component che connette Claude-Code-Usage-Monitor con il sistema hooks esistente.

## 🎯 Obiettivo

Prevenire e gestire automaticamente:
- **Rate Limits**: Exponential backoff automatico
- **Time Limits**: Session pause/resume intelligente  
- **Cost Limits**: Graceful degradation
- **Token Limits**: Alert proattivi

## 🏗️ Architettura

```
Claude Code → Python Hooks → Bun Server :4000 → Bridge Component → Usage Monitor + Auto Recovery + Dashboard
```

**Componenti:**
- **Bridge Component** (`bridge.py`): Python bridge che collega i sistemi
- **Sistema Hooks**: Bun server + SQLite + Vue client (esistente)
- **Usage Monitor**: Python CLI + analytics (repository esistente)

## 🚀 Quick Start

### Prerequisiti
```bash
# Python 3.7+
python3 --version

# Sistema hooks attivo su :4000
cd ../apps/server && bun run dev
```

### 🚀 Installazione Automatica
```bash
# Script di avvio con auto-setup completo
./start.sh

# Include automaticamente:
# - Installazione uv (se necessario)
# - Installazione claude-monitor via uv
# - Installazione dipendenze Python
# - Verifica sistema completo
```

### 📋 Installazione Manuale (opzionale)
```bash
# 1. Installa uv (raccomandato)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Installa claude-monitor
uv tool install claude-monitor

# 3. Installa dipendenze Python
pip3 install -r requirements.txt

# 4. Avvia bridge
python3 bridge.py
```

### Verifica Funzionamento
```bash
# Health check
curl http://localhost:8080/health

# Metrics unificati
curl http://localhost:8080/metrics

# Test alert manuale
curl -X POST http://localhost:8080/alerts/test_alert
```

## ⚙️ Configurazione

### `config.yaml` - Alert Thresholds
```yaml
alerts:
  token_threshold: 0.8      # Alert al 80% utilizzo token
  time_threshold: 4.5       # Pausa a 4.5 ore
  cost_threshold: 50.0      # Alert a $50
  rate_limit_threshold: 0.9 # Alert al 90% rate limit
```

### Recovery Strategies
```yaml
recovery:
  rate_limit: "exponential_backoff"  # Backoff per rate limits
  time_limit: "session_pause"        # Pausa per time limits  
  cost_limit: "graceful_degradation" # Degradazione per costi
  auto_recovery: true                # Recovery automatico
```

## 📊 API Endpoints

### GET `/metrics`
Metriche unificate da entrambi i sistemi:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "hooks_data": {...},      // Real-time da hooks system
  "usage_data": {...},      // Analytics da Usage Monitor
  "recovery_state": "normal",
  "active_alerts": {...}
}
```

### GET `/health`
Stato di salute del sistema:
```json
{
  "status": "healthy",
  "websocket": "connected",
  "recovery_state": "normal",
  "alerts_count": 0
}
```

### POST `/alerts/{alert_type}`
Trigger manuale alert (per testing):
```bash
curl -X POST http://localhost:8080/alerts/rate_limit
```

### GET `/recovery/status`
Stato recovery attuale:
```json
{
  "state": "normal",
  "active_alerts": {},
  "timestamp": "2024-01-15T10:30:00"
}
```

## 🔧 Integrazione Esistente

### Nessuna Modifica Richiesta
Il bridge si integra **senza modificare** i sistemi esistenti:

✅ **Bun Server** (porta :4000)
- WebSocket endpoint: `/stream`
- SQLite database: `events.db`
- API endpoints esistenti

✅ **Usage Monitor** (CLI)
- Comando: `claude-monitor`
- Analytics: P90 calculations
- Output: Terminal UI + structured data

### Punti di Connessione
1. **WebSocket** → Bun server :4000/stream (real-time events)
2. **Subprocess** → claude-monitor CLI (analytics polling)
3. **REST API** → Bridge API :8080 (unified access)

## ⚡ Flusso Operativo

### 1. Monitoring Attivo
- **Real-time**: WebSocket events da hooks system
- **Analytics**: Polling Usage Monitor ogni 30s
- **Correlation**: Merge dati per insight completi

### 2. Alert Logic
```python
if token_usage > 80%:     → Alert "token_threshold"
if session_time > 4.5h:   → Alert "time_limit" 
if total_cost > $50:      → Alert "cost_threshold"
if rate_limit > 90%:      → Alert "rate_limit"
```

### 3. Auto Recovery
- **Rate Limit** → Exponential backoff (1s, 2s, 4s, 8s, 16s, 32s)
- **Time Limit** → Session pause + notification (resume next day)
- **Cost Limit** → Graceful degradation (reduced functionality)

## 📈 Dashboard Integration

### Opzioni Disponibili

**Current (Phase 1)**: Bridge REST API
```bash
# Accesso diretto ai dati via API
curl http://localhost:8080/metrics | jq
```

**Future (Phase 2)**: Grafana Integration
```yaml
# Grafana data source configuration
- name: Claude Bridge
  type: prometheus
  url: http://localhost:8080/prometheus
```

**Future (Phase 3)**: Vue.js Integration
```javascript
// Integrazione con Vue client esistente
const bridgeMetrics = await fetch('http://localhost:8080/metrics')
```

## 🛠️ Troubleshooting

### Bridge Non Si Connette
```bash
# Verifica Bun server attivo
curl http://localhost:4000/health

# Verifica WebSocket disponibile  
wscat -c ws://localhost:4000/stream

# Check logs bridge
tail -f bridge.log
```

### Usage Monitor Non Funziona
```bash
# Test CLI diretto (dovrebbe funzionare ovunque)
claude-monitor --help

# Se non trovato, installa con uv
uv tool install claude-monitor

# Verifica integrazione bridge
./check_system.sh

# Test manuale command nel working dir
cd /Users/sam/Claude-Code-Usage-Monitor
claude-monitor --view session
```

### API Non Risponde
```bash
# Verifica porta occupata
lsof -i :8080

# Restart bridge
python3 bridge.py
```

## 📝 Development

### Testing
```bash
# Unit tests
python3 -m pytest

# Integration test con WebSocket mock
python3 -m pytest test_websocket.py

# Load testing
python3 -m pytest test_recovery.py
```

### Logging
```bash
# Debug mode
export LOG_LEVEL=DEBUG
python3 bridge.py

# Monitor logs real-time
tail -f bridge.log | grep "ALERT"
```

## 🔄 Roadmap

### ✅ Phase 1 - Core Bridge + Usage Monitor (COMPLETED)
- WebSocket client per Bun server
- Usage Monitor CLI integration with **uv tool install**
- API REST completa con root endpoint
- Alert system con auto-recovery
- Auto-installation scripts con uv
- Sistema di testing completo
- Documentazione aggiornata

### ⏸️ Phase 2 - Enhanced Monitoring (NEXT)
- Advanced metrics correlation
- Grafana/Prometheus integration
- Performance optimization
- Enhanced recovery strategies

### 📋 Phase 3 - Production Ready (FUTURE)
- Vue.js dashboard integration
- Advanced notification system
- Multi-session support
- Cloud deployment ready

## 💡 Perfect Use Case

**Scenario che ha motivato questo bridge:**
Durante l'implementazione di questo stesso sistema, abbiamo raggiunto il rate limit di Claude AI. Il bridge avrebbe:

1. **Rilevato** il limite in avvicinamento (80% threshold)
2. **Allertato** automaticamente l'utente
3. **Avviato** exponential backoff recovery
4. **Ripristinato** la sessione seamlessly
5. **Loggiato** tutto per analysis

**Risultato**: Zero interruzioni, workflow continuo, esperienza utente ottimale.

---
*Implementazione completata come dimostrazione pratica della necessità del sistema stesso! 🎯*