# 🚀 GitHub Copilot Code Review - Setup Completo

## 📋 Prerequisiti

### Account Requirements
- **GitHub Copilot Pro/Pro+** subscription attiva
- **Repository admin access** per configurazione rulesets
- **GitHub CLI** installato e autenticato

### Verifica Setup
```bash
# Verifica GitHub CLI
gh --version

# Verifica autenticazione
gh auth status

# Installa Copilot CLI extension
gh extension install github/gh-copilot

# Verifica Copilot CLI
gh copilot --help
```

## 🎯 Configurazione Automatica per Repository

### Metodo 1: Via Web Interface (UI)

#### Step 1: Repository Settings
1. Vai alla repository su GitHub.com
2. Click **Settings** (tab in alto)
3. Nel sidebar sinistro: **Code and automation** → **Rules** → **Rulesets**
4. Click **New ruleset** → **New branch ruleset**

#### Step 2: Configurazione Ruleset
```yaml
Ruleset Name: "Copilot Auto Review"
Enforcement Status: "Active"
Target Branches: 
  - "Include default branch" (main/master)
  - "Include all branches" (opzionale)

Protection Rules:
☑️ "Request pull request review from Copilot"
```

#### Step 3: Save Configuration
- Click **Create** in fondo alla pagina
- Il ruleset sarà attivo immediatamente

### Metodo 2: Via GitHub CLI (Automatizzabile)

#### Setup Repository Ruleset
```bash
# Configurazione via CLI (richiede gh CLI v2.40+)
gh api repos/:owner/:repo/rulesets \
  --method POST \
  --field name="Copilot Auto Review" \
  --field enforcement="active" \
  --field target='{"include":[{"type":"branch","value":"**"}]}' \
  --field rules='[{"type":"pull_request","parameters":{"required_approving_review_count":0,"require_code_owner_review":false,"copilot_review_required":true}}]'
```

#### Verifica Configurazione
```bash
# Lista rulesets attivi
gh api repos/:owner/:repo/rulesets --jq '.[].name'

# Dettagli ruleset specifico
gh api repos/:owner/:repo/rulesets/:ruleset_id
```

### Metodo 3: Configurazione via Git Hooks (Avanzato)

#### Pre-push Hook Setup
```bash
# Crea pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/sh
# Verifica che Copilot review sia abilitato prima del push

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo "🤖 Copilot Review attivato per branch: $BRANCH"
    # Forza creazione PR con richiesta Copilot review
    gh pr create --draft --title "Draft: $BRANCH" --body "@copilot review" 2>/dev/null || true
fi
EOF

chmod +x .git/hooks/pre-push
```

## 🔄 Automazione Workflow Completa

### GitHub Action per Auto-Review
```yaml
# .github/workflows/copilot-review.yml
name: Copilot Auto Review

on:
  pull_request:
    types: [opened, synchronize, ready_for_review]

jobs:
  copilot-review:
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false
    
    steps:
    - name: Request Copilot Review
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        gh pr comment ${{ github.event.pull_request.number }} \
          --body "@copilot review this code for security, performance, and best practices"
        
    - name: Add Review Labels
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        gh pr edit ${{ github.event.pull_request.number }} \
          --add-label "copilot-review-requested"
```

### Custom Instructions File
```bash
# Crea copilot-instructions.md nella root del repository
cat > copilot-instructions.md << 'EOF'
# Copilot Code Review Instructions

## Review Focus Areas
- Security vulnerabilities and best practices
- Performance optimizations and bottlenecks
- Code maintainability and readability
- Error handling and edge cases
- Type safety and documentation quality

## Project-Specific Guidelines
- Follow PEP 8 for Python code
- Use type hints consistently
- Ensure comprehensive test coverage
- Document public APIs thoroughly
- Validate input parameters

## Review Criteria
- Rate security: 1-10 (8+ required)
- Rate performance: 1-10 (7+ required)  
- Rate maintainability: 1-10 (8+ required)
- Flag any breaking changes
- Suggest optimizations where applicable
EOF
```

## 🎛️ Configurazione Organization-Level

### Setup per Multiple Repositories
```bash
# Script per configurazione batch repositories
#!/bin/bash
REPOS=("repo1" "repo2" "repo3")  # Lista repository
ORG="your-organization"

for repo in "${REPOS[@]}"; do
    echo "Configurando $repo..."
    gh api repos/$ORG/$repo/rulesets \
      --method POST \
      --field name="Copilot Auto Review" \
      --field enforcement="active" \
      --field target='{"include":[{"type":"branch","value":"**"}]}' \
      --field rules='[{"type":"pull_request","parameters":{"copilot_review_required":true}}]'
done
```

### Organization Settings
1. GitHub.com → Your organizations → [Org Name] → Settings
2. Repository → Rulesets → New ruleset → New branch ruleset
3. Repository targeting: "All repositories" o pattern specifici
4. ☑️ "Request pull request review from Copilot"

## 🔧 Integrazione con Multi-Agent System

### github-copilot-reviewer Agent Integration
```bash
# Comandi per automazione nel nostro agent
gh pr create --title "$PR_TITLE" --body "@copilot review"
gh pr comment --body "@copilot explain this suggestion"
gh pr status --json reviews | jq '.reviews[] | select(.author.login == "github-copilot")'
```

### Workflow Script Completo
```bash
#!/bin/bash
# copilot-review-automation.sh

BRANCH=$(git rev-parse --abbrev-ref HEAD)
PR_TITLE="feat: $BRANCH implementation"

# 1. Push branch
git push -u origin $BRANCH

# 2. Create PR with Copilot review request
PR_URL=$(gh pr create \
  --title "$PR_TITLE" \
  --body "$(cat <<EOF
## Summary
Automated PR from multi-agent system

## Changes Made
$(git diff --name-only HEAD~1)

## Review Focus
- Security validation
- Performance optimization  
- Code quality standards

@copilot review this code thoroughly
EOF
)")

echo "PR created: $PR_URL"

# 3. Monitor review status
gh pr view --json reviews | jq -r '.reviews[] | "\(.author.login): \(.state)"'
```

## 📊 Verifica e Monitoring

### Status Check Commands
```bash
# Verifica ruleset attivo
gh api repos/:owner/:repo/rulesets --jq '.[].name'

# Check PR reviews
gh pr list --json reviews --jq '.[] | select(.reviews[].author.login == "github-copilot")'

# Monitor review completion
gh pr checks --required-only
```

### Dashboard Metrics
```bash
# Script per metrics collection
#!/bin/bash
echo "🤖 Copilot Review Metrics"
echo "========================"

TOTAL_PRS=$(gh pr list --state all --json number | jq length)
COPILOT_REVIEWS=$(gh pr list --state all --json reviews | jq '[.[] | select(.reviews[].author.login == "github-copilot")] | length')

echo "Total PRs: $TOTAL_PRS"
echo "Copilot Reviews: $COPILOT_REVIEWS"
echo "Coverage: $(echo "scale=2; $COPILOT_REVIEWS * 100 / $TOTAL_PRS" | bc)%"
```

## 🚨 Troubleshooting

### Common Issues
```bash
# 1. Verifica subscription Copilot
gh copilot --help

# 2. Check repository permissions
gh api user/repos --jq '.[] | select(.name=="repo-name") | .permissions'

# 3. Verifica rulesets attivi
gh api repos/:owner/:repo/rulesets --jq '.[].enforcement'

# 4. Debug webhook events
gh api repos/:owner/:repo/hooks --jq '.[].events'
```

### Fix Permission Issues
```bash
# Se mancano permessi per rulesets
gh auth refresh --scopes repo,admin:repo_hook,admin:org

# Re-authenticate con scope estesi
gh auth login --scopes repo,admin:repo_hook,admin:org
```

---

## ✅ Checklist Implementazione

- [ ] GitHub Copilot Pro subscription attiva
- [ ] GitHub CLI installato e autenticato
- [ ] gh-copilot extension installata
- [ ] Repository ruleset configurato
- [ ] copilot-instructions.md creato
- [ ] GitHub Action workflow attivo
- [ ] Integration testing completato
- [ ] Team training su nuovo workflow

**Il sistema è ora completamente automatizzato per Copilot Code Review!**