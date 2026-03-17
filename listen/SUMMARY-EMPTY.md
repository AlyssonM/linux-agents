# ✅ SIM, deveria mostrar a resposta!

## Problema identificado

```yaml
id: f84c3a19
status: completed
prompt: ping
agent: opencode
exit_code: 0
summary: ''  # ❌ VAZIO (mas não deveria!)
```

## Por que isso acontece

O `_run_opencode()` **não captura o output** do tmux como o `_run_codex()` faz.

### Comparação

**codex** ✅ (funciona):
- Usa arquivo de output: `-o output.txt`
- Lê arquivo no finally
- Salva em summary

**opencode** ❌ (não funciona):
- Executa na sessão tmux
- **Não captura output**
- Tenta ler arquivo do codex (não existe)
- Summary fica vazio

## Solução

Adicionar captura do tmux no finally:

```python
# Capturar summary para opencode/openclaw
elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
    captured = _capture_pane(session_name)

    # Filtrar linhas úteis
    useful = []
    for line in captured.split('\n'):
        if SENTINEL_PREFIX in line:
            continue
        if line.strip().startswith(('$', '>', 'alyssonpi@', '/')):
            continue
        if not line.strip():
            continue
        useful.append(line.rstrip())

    # Pegar últimas 20 linhas
    if useful:
        data["summary"] = '\n'.join(useful[-20:])[:4000]
```

## Exemplo esperado

**Prompt:** `ping`

**Output do tmux:**
```
/home/alyssonpi/.opencode/bin/opencode run ping ; echo "__JOBDONE_xxx:$?"
> build · glm-4.5-air
pong
__JOBDONE_xxx:0
```

**Summary limpo:**
```yaml
summary: 'pong'  # ✅ Conteúdo capturado!
```

## Documentação

Veja **`SUMMARY-FIX.md`** para:
- Explicação detalhada do problema
- 3 soluções possíveis
- Código completo de implementação
- Exemplos de output

## Status

⏳ **Aguardando implementação da correção**

Por enquanto, para ver a resposta do job:
1. Ver o arquivo YAML manualmente
2. Fazer attach na sessão tmux (se ainda existir)
3. Implementar a correção sugerida em `SUMMARY-FIX.md`
