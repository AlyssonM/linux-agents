# Problema: Summary vazio em jobs opencode

## Caso real

```yaml
id: f84c3a19
status: completed
prompt: ping
agent: opencode
exit_code: 0
summary: ''  # ❌ VAZIO! Deveria mostrar a resposta do opencode
```

## Causa

O `_run_opencode()` não captura o output da sessão tmux como o `_run_codex()` faz.

### Comparação

**codex** (funciona):
```python
def _run_codex(...):
    # Escreve output em arquivo
    codex_cmd += f"-o '{output_file}'"

    # No finally, lê o arquivo
    output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
    if output_file.exists():
        data["summary"] = output_file.read_text().strip()[:4000]
```

**opencode** (não captura):
```python
def _run_opencode(...):
    # Executa na sessão tmux
    _send_keys(session_name, wrapped_cmd)

    # ❌ Não captura output!
    # No finally, só tenta ler arquivo do codex
    output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
    if output_file.exists():  # Sempre false para opencode!
        data["summary"] = ...
```

## Solução 1: Capturar output do tmux

Adicionar captura no finally:

```python
# No finally, após try/except
finally:
    duration = round(time.time() - start_time)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = _read_yaml(job_file)

    if data.get("status") == "running":
        data["status"] = "completed" if exit_code == 0 else "failed"
        data["exit_code"] = exit_code
        data["duration_seconds"] = duration
        data["completed_at"] = now

        # Capturar summary para todos os agentes
        if not data.get("summary"):
            if agent == "codex":
                output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
                if output_file.exists():
                    data["summary"] = output_file.read_text(encoding="utf-8").strip()[:4000]
            else:
                # Capturar do tmux para opencode/openclaw
                if _session_exists(session_name):
                    captured = _capture_pane(session_name)
                    # Remover linhas de comando e sentinela
                    lines = [l for l in captured.split('\n')
                            if l.strip() and
                            SENTINEL_PREFIX not in l and
                            not l.strip().startswith('/')]
                    # Pegar últimas N linhas (úteis)
                    useful_lines = [l for l in lines if l.strip()]
                    if useful_lines:
                        data["summary"] = '\n'.join(useful_lines[-20:])[:4000]

        _write_yaml(job_file, data)
```

## Solução 2: Usar arquivo de output para opencode

```python
def _run_opencode(job_id: str, prompt: str, model: str, session_name: str) -> int:
    """Run job using OpenCode CLI."""
    token = uuid.uuid4().hex[:8]
    output_file = Path(f"/tmp/listen-opencode-output-{job_id}.txt")

    opencode_bin = Path.home() / ".opencode" / "bin" / "opencode"

    if not opencode_bin.exists():
        raise FileNotFoundError(f"OpenCode binary not found at {opencode_bin}")

    # Redirecionar output para arquivo
    opencode_cmd = [
        "script", "-q", "-c",  # Captura output
        f"{opencode_bin} run {prompt}",
        str(output_file)
    ]

    wrapped = f'{" ".join(opencode_cmd)} ; echo "{SENTINEL_PREFIX}{token}:$?"'

    _ensure_session(session_name, str(REPO_ROOT))
    _send_keys(session_name, wrapped)
    return _wait_for_sentinel(session_name, token)
```

## Solução 3: Capturar do tmux (RECOMENDADO)

Mais simples, funciona para opencode e openclaw:

```python
# No finally
else:
    # Capturar output do tmux para opencode/openclaw
    if agent in ["opencode", "openclaw"] and _session_exists(session_name):
        captured = _capture_pane(session_name)

        # Limpar output
        lines = captured.split('\n')
        useful_lines = []

        for line in lines:
            line = line.rstrip()
            # Pular linhas vazias
            if not line:
                continue
            # Pular prompt/command
            if line.strip().startswith('$') or line.strip().startswith('>'):
                continue
            # Pular sentinel
            if SENTINEL_PREFIX in line:
                continue
            useful_lines.append(line)

        # Pegar últimas 20 linhas úteis
        if useful_lines:
            data["summary"] = '\n'.join(useful_lines[-20:])[:4000]
```

## Exemplo de output esperado

**Input:**
```yaml
prompt: ping
```

**Output capturado do tmux:**
```
alyssonpi@alyssonpi4:~/.openclaw/workspace/linux-agents $ /home/alyssonpi/.opencode/bin/opencode run ping ; echo "__JOBDONE_xxx:$?"

> build · glm-4.5-air

pong

__JOBDONE_xxx:0
```

**Summary limpo:**
```yaml
summary: 'pong'
```

## Implementação

Editar `worker.py` no bloco `finally`:

```python
finally:
    duration = round(time.time() - start_time)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = _read_yaml(job_file)

    if data.get("status") == "running":
        data["status"] = "completed" if exit_code == 0 else "failed"
        data["exit_code"] = exit_code
        data["duration_seconds"] = duration
        data["completed_at"] = now

        # Capturar summary
        if not data.get("summary"):
            if agent == "codex":
                output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
                if output_file.exists():
                    data["summary"] = output_file.read_text(encoding="utf-8").strip()[:4000]
            elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
                captured = _capture_pane(session_name)
                lines = [l.rstrip() for l in captured.split('\n') if l.strip()]

                # Filtrar linhas úteis
                useful = []
                for line in lines:
                    if SENTINEL_PREFIX in line:
                        continue
                    if line.strip().startswith('$'):
                        continue
                    if line.strip().startswith('>'):
                        continue
                    if line.strip().startswith('alyssonpi@'):
                        continue
                    if line.strip().startswith('/'):
                        continue
                    useful.append(line)

                if useful:
                    data["summary"] = '\n'.join(useful[-20:])[:4000]

        _write_yaml(job_file, data)
```

## Testar

```bash
# Criar job de teste
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say TEST", "agent": "opencode"}'

# Aguardar completar
sleep 10

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
