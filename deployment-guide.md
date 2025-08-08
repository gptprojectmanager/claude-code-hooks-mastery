# claude-code-router + liteLLM Integration Guide

## Architettura Soluzione

```
Claude Code → claude-code-router → liteLLM Proxy → Gemini API
                    (port 3456)      (port 4000)     (Google)
```

### Componenti
- **claude-code-router**: Proxy che traduce richieste Anthropic → OpenAI format
- **liteLLM**: Gateway che normalizza schema tools e gestisce provider multipli  
- **Gemini 2.5 Pro/Flash**: Modelli target con schema translation automatica

## Problema Risolto

Il tallone d'Achille di ccr è l'errore `exclusiveMinimum` nei tool schema MCP:
- ccr trasforma male gli schemi verso Gemini
- liteLLM fornisce normalizzazione robusta cross-provider
- Risolve incompatibilità come `exclusiveMinimum` non supportato da Gemini

## File Creati

1. **litellm-ccr-config.yaml**: Configurazione liteLLM proxy
2. **ccr-litellm-integration.json**: Config ccr per usare liteLLM
3. **setup-ccr-litellm.sh**: Script setup automatico
4. **start-litellm.sh**: Avvia proxy liteLLM
5. **start-ccr.sh**: Avvia claude-code-router
6. **test-integration.sh**: Test configurazione

## Deployment Steps

```bash
# 1. Setup iniziale
./setup-ccr-litellm.sh

# 2. Configurare API keys in .env.ccr-litellm
# GEMINI_API_KEY=your-actual-key

# 3. Avviare servizi (terminali separati)
./start-litellm.sh    # Terminal 1
./start-ccr.sh        # Terminal 2  

# 4. Test
./test-integration.sh

# 5. Usare claude-code
ccr code
```

## Success Criteria

✅ claude-code funziona con Gemini Pro/Flash 2.5
✅ Nessun errore `exclusiveMinimum` o schema incompatibility  
✅ MCP tools tradotti correttamente
✅ Fallback automatico tra modelli configurabili