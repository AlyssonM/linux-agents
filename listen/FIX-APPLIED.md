# ✅ Fix aplicado: Capturar tmux output para summary

## Mudança implementada

Arquivo: `listen/worker.py`

**Antes:**
```python
# Try to read output file for codex
output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
if output_file.exists() and not data.get("summary"):
    data["summary"] = output_file.read_text(encoding="utf-8").strip()[:4000]
```

**Depois:**
```python
# Capture summary if not already set
if not data.get("summary"):
    if agent == "codex":
        # Read output file for codex
        output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
        if output_file.exists():
            data["summary"] = output_file.read_text(encoding="utf-8").strip()[:4000]
    elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
        # Capture tmux output for opencode/openclaw
        captured = _capture_pane(session_name)
        lines = []

        for line in captured.split('\n'):
            line = line.rstrip()
            # Skip empty lines
            if not line:
                continue
            # Skip sentinel
            if SENTINEL_PREFIX in line:
                continue
            # Skip command prompts
            if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@', '/']):
                continue
            lines.append(line)

        # Take last 20 useful lines
        if lines:
            data["summary"] = '\n'.join(lines[-20:])[:4000]
```

## O que foi adicionado

1. ✅ **Captura do tmux** para opencode/openclaw
2. ✅ **Filtro de linhas úteis** (remove prompts, sentinelas, vazias)
3. ✅ **Limite de linhas** (últimas 20)
4. ✅ **Limite de caracteres** (max 4000)

## Teste

```bash
# Criar job de teste
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say TEST", "agent": "opencode"}'

# Aguardar
sleep 15

# Ver summary
curl http://localhost:7600/job/<JOB_ID> | grep summary
```

## Esperado

```yaml
summary: 'TEST'  # ✅ Conteúdo capturado!
```

Em vez de:
```yaml
summary: ''  # ❌ Vazio
```

## Situação atual

⏳ **Serviço reiniciando**

Aguardando systemd service iniciar para testar.

## Documentação relacionada

- **SUMMARY-FIX.md** - Solução completa
- **SUMMARY-EMPTY.md** - Explicação do bug
- **SUMMARY-BUG.md** - Referência rápida
