# 🚀 Quick Setup GitHub Copilot Review

## 📋 Status Attuale
- ✅ GitHub CLI installato via MacPorts (`/opt/local/bin/gh`)
- ✅ Repository clonata: `claude-code-hooks-mastery`
- ✅ Git configurato con `gptprojectmanager@gmail.com`
- ⏳ Autenticazione GitHub CLI in corso

## 🔑 Passo 1: Completare Autenticazione
**Codice generato:** `B510-2045`
**URL:** https://github.com/login/device

1. Apri il link nel browser
2. Inserisci il codice `B510-2045`
3. Autorizza con account `gptprojectmanager@gmail.com`
4. Conferma permessi richiesti

## 🍴 Passo 2: Fork Repository (Dopo Autenticazione)
```bash
# Aggiungi MacPorts al PATH
export PATH="/opt/local/bin:$PATH"

# Verifica autenticazione
gh auth status

# Fork repository originale
gh repo fork disler/claude-code-hooks-mastery --clone=false

# Aggiorna remote
git remote set-url origin https://github.com/gptprojectmanager/claude-code-hooks-mastery.git
git remote add upstream https://github.com/disler/claude-code-hooks-mastery.git
```

## 🤖 Passo 3: Setup Copilot
```bash
# Installa estensione Copilot
gh extension install github/gh-copilot

# Verifica funzionamento
gh copilot --help

# Configura auto-review sul fork
gh api repos/gptprojectmanager/claude-code-hooks-mastery/rulesets \
  --method POST \
  --field name="Copilot Auto Review" \
  --field enforcement="active" \
  --field target='{"include":[{"type":"branch","value":"**"}]}' \
  --field rules='[{"type":"pull_request","parameters":{"copilot_review_required":true}}]'
```

## 🧪 Passo 4: Test Workflow
```bash
# Crea branch di test
git checkout -b test/copilot-review-setup

# Crea file di test
echo "# Test Copilot Review" > test-copilot.md
echo "Questo file testa l'integrazione Copilot review." >> test-copilot.md

# Commit e push
git add test-copilot.md
git commit -m "test: setup Copilot review integration"
git push -u origin test/copilot-review-setup

# Crea PR con richiesta Copilot review
gh pr create \
  --title "Test: Copilot Review Integration" \
  --body "🤖 Test dell'integrazione automatica di GitHub Copilot code review.

@copilot review this implementation for:
- Configuration correctness
- Documentation quality  
- Integration patterns

Questo è un test del sistema dual-review implementato."

# Monitora PR
gh pr view --web
```

## 📁 File Già Creati
- ✅ `copilot-instructions.md` - Istruzioni personalizzate per review
- ✅ `.github/workflows/copilot-review.yml` - GitHub Action automatica
- ✅ `setup-fork-copilot.sh` - Script automatico completo

## 🔄 Automatizzazione Completa
Una volta completati i passi sopra, ogni PR futura attiverà automaticamente:
1. GitHub Action che richiede Copilot review
2. Ruleset che richiede review prima del merge
3. Workflow dual-review: code-reviewer agent + Copilot

## 📊 Verifica Success
```bash
# Check ruleset attivo
gh api repos/gptprojectmanager/claude-code-hooks-mastery/rulesets --jq '.[].name'

# Verifica estensioni
gh extension list

# Test Copilot
gh copilot suggest "create a python script to test GitHub API"
```