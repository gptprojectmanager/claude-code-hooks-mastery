# 🛡️ Claude Configuration Guardian

## ⚠️ PROBLEMA RISOLTO: Bug Noto di Claude Code

**Il tuo .claude.json viene cancellato perché è un BUG DOCUMENTATO di Claude Code!**

### Issues GitHub Ufficiali:
- **#1788**: "MCP Configuration Unexpectedly Deleted From File During Auto-Update"  
- **#2763**: "[BUG] .claude.json MCP global configs = empty"
- **#1676**: "Persistent Logout & Configuration Loss Bug Report"

**Claude Code cancella automaticamente le configurazioni MCP durante gli aggiornamenti!**

---

## 🚑 SOLUZIONE IMPLEMENTATA

### 1. Guardian Automatico
```bash
# Monitora continuamente .claude.json
./scripts/claude-config-guardian.sh guard
```

**Protezioni attive:**
- ✅ **Anti-corruption backup**: Backup SOLO se file valido (impedisce sovrascrittura backup buoni)
- ✅ **Real-time monitoring**: fswatch per rilevamento immediato corruzioni
- ✅ **Auto-restore**: Ripristino automatico da backup validi
- ✅ **Timestamp backup**: Nome file con data/ora leggibile
- ✅ **Project-level backup**: Backup locale + globale

### 2. Smart Restore (Integrato nel Guardian)
```bash
# Ripristino integrato - automatico o manuale
./scripts/claude-config-guardian.sh restore
```

### 3. LaunchAgent (Sempre Attivo)
```bash
# Carica servizio automatico macOS
launchctl load ~/Library/LaunchAgents/com.claude.config.guardian.plist
```

---

## 📁 STRUTTURA BACKUP

```
~/.claude-backups/                         # ← Directory backup (correzione path)
├── claude_20250904_223045_startup.json    # ← Backup con timestamp
├── claude_20250904_223156_change.json
├── claude_20250904_223298_manual.json
└── ...

PROJECT/.claude-backup.json                # ← Backup progetto locale
```

### Formato Nome Backup:
- `claude_YYYYMMDD_HHMMSS_REASON.json`
- **Date leggibili nei log**: `2025-09-04_22:30:45`
- **Motivi**: startup, change, manual, recovery

---

## 🔧 COMANDI DISPONIBILI

### Guardian Management
```bash
./scripts/claude-config-guardian.sh guard         # Avvia monitoring
./scripts/claude-config-guardian.sh backup        # Backup manuale
./scripts/claude-config-guardian.sh restore       # Ripristino da backup
./scripts/claude-config-guardian.sh status        # Stato sistema
./scripts/claude-config-guardian.sh list-backups  # Lista backup disponibili
```

### Recovery Commands  
```bash
./scripts/claude-config-guardian.sh restore       # Ripristino intelligente
./scripts/claude-config-guardian.sh status        # Stato sistema completo
launchctl list | grep claude                      # Verifica servizio attivo
```

---

## 🛡️ PROTEZIONI IMPLEMENTATE

### 1. **Validation-First Backup**
```bash
# CRITICA: Solo backup se config VALIDO
if is_config_valid "$CLAUDE_JSON"; then
    cp "$CLAUDE_JSON" "$backup_file"  # ← Backup
    log "✅ Valid backup created"
else
    error "🚨 REFUSING to backup corrupted file!"  # ← Impedisce sovrascrittura
fi
```

### 2. **Real-Time Detection**
- **fswatch monitoring**: Rilevamento cambiamenti istantaneo
- **Automatic validation**: Controllo validità dopo ogni modifica
- **Immediate restore**: Ripristino automatico se corrupted

### 3. **Multi-Layer Recovery**
1. **Project backup**: `.claude-backup.json` (priorità)
2. **Latest backup**: Backup più recente valido
3. **Manual selection**: Scelta backup specifico

---

## 🔍 DIAGNOSI E DEBUG

### Status Check
```bash
./scripts/claude-config-guardian.sh status
# Output:
# 📊 Claude Configuration Status:
# Main config: ✅ Valid (16 servers)
# Project backup: ✅ Valid  
# Available backups: 5
```

### Log Monitoring
```bash
# Guardian logs
tail -f ~/.claude-logs/guardian-stdout.log

# LaunchAgent status  
launchctl list com.claude.config.guardian
```

### Recovery Process
```bash
# 1. Automatic intelligent restore
./scripts/claude-config-guardian.sh restore

# 2. Manual backup selection (se necessario)
./scripts/claude-config-guardian.sh restore ~/.claude-backups/claude_TIMESTAMP_reason.json

# 3. Verify restoration
./scripts/claude-config-guardian.sh status
```

---

## 🚨 QUANDO ATTIVARSI

### Sintomi di Corruzione:
- `.claude.json` < 1KB (dovrebbe essere ~5KB)
- MCP servers < 10 (dovresti averne 16+)
- `/mcp` comando mostra "No servers"
- Claude Code chiede riconfigurazione MCP

### Azione Immediata:
```bash
# ⚡ Un solo comando risolve tutto
./scripts/claude-emergency-restore.sh
```

---

## 🎯 CONFIGURAZIONE COMPLETATA

### ✅ Protezioni Attive:
- [x] Guardian daemon (LaunchAgent)
- [x] Real-time monitoring (fswatch)  
- [x] Anti-corruption backup
- [x] Auto-restore capabilities
- [x] Emergency recovery scripts
- [x] Multi-layer backup strategy

### 📍 Files Installati:
- `scripts/claude-config-guardian.sh` - Guardian principale
- `scripts/claude-emergency-restore.sh` - Emergency restore  
- `~/Library/LaunchAgents/com.claude.config.guardian.plist` - LaunchAgent
- `~/claude_backups/` - Directory backup
- `.claude-backup.json` - Backup locale progetto

### 🎉 RISULTATO:
**Non perderai mai più la configurazione .claude.json!**

Il sistema ora protegge automaticamente contro il bug di Claude Code, garantendo sempre backup validi e ripristino automatico.

---

*Sistema implementato e testato - Bug #1788 di Claude Code neutralizzato! 🛡️*