#!/bin/bash

# Script per rimuovere la chiave API dalla cronologia Git
# ATTENZIONE: Questo riwrite della cronologia Git!

set -e

echo "⚠️  ATTENZIONE: Questo script riscrive la cronologia Git!"
echo "📋 Creerà backup e pulirà la chiave API da tutti i commit"

# Backup del repository
echo "💾 Creazione backup..."
cp -r . ../claude-code-hooks-mastery-backup-$(date +%Y%m%d_%H%M%S)

# Trova tutti i commit che contengono la chiave
echo "🔍 Ricerca commit contenenti la chiave..."
git log --all --full-history --oneline --grep="AIzaSyC51zw_xZxHw12YOmRdb-H3WwB8N8pbCnM" || true
git log --all --full-history --oneline -S "AIzaSyC51zw_xZxHw12YOmRdb-H3WwB8N8pbCnM" || true

echo ""
echo "🧹 Rimozione chiave API dalla cronologia..."

# Usa git filter-branch per rimuovere la chiave da tutti i commit
git filter-branch --force --index-filter \
  'git ls-files -s | sed "s/AIzaSyC51zw_xZxHw12YOmRdb-H3WwB8N8pbCnM/REDACTED_API_KEY/g" |
   GIT_INDEX_FILE=$GIT_INDEX_FILE.new git update-index --index-info &&
   mv $GIT_INDEX_FILE.new $GIT_INDEX_FILE' HEAD

# Rimuove i riferimenti al vecchio albero
echo "🗑️  Cleanup riferimenti..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ Pulizia cronologia Git completata!"
echo "⚠️  IMPORTANTE: Dovrai fare force push per aggiornare GitHub:"
echo "   git push origin --force --all"
echo ""
echo "💾 Backup salvato in: ../claude-code-hooks-mastery-backup-*"