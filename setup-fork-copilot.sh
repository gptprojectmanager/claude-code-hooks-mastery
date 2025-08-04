#!/bin/bash

# 🍴 Fork Repository e Setup Copilot Review
# Configura fork personale per testing Copilot review

set -e

echo "🍴 Fork Repository e Copilot Review Setup"
echo "========================================="

# Verifica GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI non trovato. Aspetto installazione..."
    echo "💡 Esegui: brew install gh"
    exit 1
fi

echo "✅ GitHub CLI disponibile: $(gh --version | head -1)"

# 1. Autenticazione con account gptprojectmanager
echo "🔐 Configurando autenticazione per gptprojectmanager@gmail.com..."

# Verifica se già autenticato
if gh auth status 2>/dev/null | grep -q "gptprojectmanager"; then
    echo "✅ Già autenticato come gptprojectmanager"
else
    echo "🔑 Autenticazione richiesta per gptprojectmanager@gmail.com"
    echo "📝 Usa le credenziali di gptprojectmanager@gmail.com"
    gh auth login --scopes repo,admin:repo_hook,admin:org
fi

# 2. Fork della repository originale
echo "🍴 Creando fork della repository..."
ORIGINAL_REPO="disler/claude-code-hooks-mastery"
FORK_REPO="gptprojectmanager/claude-code-hooks-mastery"

# Verifica se fork esiste già
if gh repo view $FORK_REPO &>/dev/null; then
    echo "✅ Fork già esistente: $FORK_REPO"
else
    echo "🔄 Creando fork..."
    gh repo fork $ORIGINAL_REPO --clone=false
    echo "✅ Fork creato: $FORK_REPO"
fi

# 3. Aggiorna remote per puntare al fork
echo "🔗 Aggiornando remote Git..."
git remote set-url origin https://github.com/$FORK_REPO.git
git remote add upstream https://github.com/$ORIGINAL_REPO.git

echo "📋 Remote configurati:"
git remote -v

# 4. Installa estensione Copilot
echo "🤖 Configurando GitHub Copilot..."
if ! gh extension list | grep -q "github/gh-copilot"; then
    gh extension install github/gh-copilot
    echo "✅ Estensione Copilot installata"
else
    echo "✅ Estensione Copilot già disponibile"
fi

# 5. Configura il fork per Copilot review
echo "⚙️ Configurando fork per Copilot auto-review..."

# Configura ruleset sul fork
gh api repos/$FORK_REPO/rulesets \
  --method POST \
  --field name="Copilot Auto Review" \
  --field enforcement="active" \
  --field target='{"include":[{"type":"branch","value":"**"}]}' \
  --field rules='[{"type":"pull_request","parameters":{"copilot_review_required":true}}]' \
  && echo "✅ Ruleset creato nel fork" \
  || echo "⚠️ Ruleset già esistente o da configurare manualmente"

# 6. Verifica configurazione
echo "🔍 Verificando configurazione fork..."
RULESETS=$(gh api repos/$FORK_REPO/rulesets --jq '.[].name' 2>/dev/null || echo "")
if echo "$RULESETS" | grep -q "Copilot Auto Review"; then
    echo "✅ Fork configurato per Copilot review"
else
    echo "⚠️ Configurazione da completare manualmente su GitHub"
fi

echo ""
echo "🎉 Setup Fork e Copilot completato!"
echo "===================================="
echo ""
echo "📁 Repository fork: https://github.com/$FORK_REPO"
echo "🔗 Remote origin: $FORK_REPO (write access)"
echo "🔗 Remote upstream: $ORIGINAL_REPO (read only)"
echo ""
echo "🧪 Test workflow:"
echo "1. git checkout -b test/copilot-review"
echo "2. # Fai modifiche al codice"
echo "3. git add . && git commit -m 'test: copilot review setup'"
echo "4. git push -u origin test/copilot-review"
echo "5. gh pr create --title 'Test: Copilot Review Integration' --body '@copilot review this implementation'"
echo "6. gh pr view --web  # Apri PR nel browser per vedere Copilot review"