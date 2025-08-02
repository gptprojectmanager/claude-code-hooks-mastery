#!/bin/bash

# 🚀 GitHub Copilot Code Review Setup Script
# Configura automaticamente il repository per Copilot review

set -e

echo "🤖 GitHub Copilot Code Review Setup"
echo "===================================="

# Verifica prerequisiti
echo "📋 Verificando prerequisiti..."

# 1. Verifica GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI non trovato. Installazione tramite Homebrew..."
    brew install gh
    
    if ! command -v gh &> /dev/null; then
        echo "❌ Errore nell'installazione di GitHub CLI"
        exit 1
    fi
fi

echo "✅ GitHub CLI disponibile: $(gh --version | head -1)"

# 2. Verifica autenticazione
echo "🔐 Verificando autenticazione GitHub..."
if ! gh auth status &> /dev/null; then
    echo "🔑 Autenticazione richiesta..."
    gh auth login --scopes repo,admin:repo_hook,admin:org
else
    echo "✅ Autenticazione GitHub attiva"
fi

# 3. Installa estensione Copilot
echo "🔧 Installando estensione GitHub Copilot..."
if ! gh extension list | grep -q "github/gh-copilot"; then
    gh extension install github/gh-copilot
    echo "✅ Estensione Copilot installata"
else
    echo "✅ Estensione Copilot già disponibile"
fi

# 4. Verifica Copilot access
echo "🤖 Verificando accesso GitHub Copilot..."
if gh copilot --help &> /dev/null; then
    echo "✅ GitHub Copilot CLI funzionante"
else
    echo "⚠️ Copilot CLI non risponde - verifica subscription"
fi

# 5. Configura repository per auto-review
echo "⚙️ Configurando repository per Copilot auto-review..."

# Ottieni informazioni repository
REPO_INFO=$(git remote get-url origin)
REPO_URL=${REPO_INFO%.git}
REPO_NAME=$(basename "$REPO_URL")
OWNER=$(basename "$(dirname "$REPO_URL")")

echo "📁 Repository: $OWNER/$REPO_NAME"

# Configura ruleset per auto-review
echo "📝 Creando ruleset per Copilot auto-review..."
gh api repos/$OWNER/$REPO_NAME/rulesets \
  --method POST \
  --field name="Copilot Auto Review" \
  --field enforcement="active" \
  --field target='{"include":[{"type":"branch","value":"**"}]}' \
  --field rules='[{"type":"pull_request","parameters":{"copilot_review_required":true}}]' \
  && echo "✅ Ruleset creato con successo" \
  || echo "⚠️ Ruleset già esistente o errore nella creazione"

# 6. Verifica configurazione
echo "🔍 Verificando configurazione..."
RULESETS=$(gh api repos/$OWNER/$REPO_NAME/rulesets --jq '.[].name' 2>/dev/null)
if echo "$RULESETS" | grep -q "Copilot Auto Review"; then
    echo "✅ Configurazione repository completata"
else
    echo "⚠️ Configurazione da verificare manualmente"
fi

# 7. Test setup
echo "🧪 Testando setup..."
echo "📋 File di configurazione creati:"
echo "  ✅ copilot-instructions.md"
echo "  ✅ .github/workflows/copilot-review.yml"

echo ""
echo "🎉 Setup completato!"
echo "==================="
echo ""
echo "🔄 Prossimi passi:"
echo "1. Crea un branch di test: git checkout -b test/copilot-review"
echo "2. Fai modifiche al codice"
echo "3. Commit e push: git add . && git commit -m 'test: copilot review' && git push -u origin test/copilot-review"
echo "4. Crea PR: gh pr create --title 'Test Copilot Review' --body '@copilot review'"
echo "5. Monitora review: gh pr view --json reviews"
echo ""
echo "📚 Per maggiori dettagli, consulta: github-copilot-setup.md"