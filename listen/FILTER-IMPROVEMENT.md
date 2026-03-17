# ❌ Problema: Summary captura comando executado

## Exemplo do problema

Job b61eac5a:
```yaml
summary: "ode/bin/opencode run Qual a fórmula de cálculo do volume do traingulo?\
 \ ; echo \"_\n_JOBDONE_7b406f1c:$?\"\nTriângulos são figuras 2D..."
```

## O que está errado

O comando executado aparece no summary:
- `ode/bin/opencode run ...` ← Remover!
- `echo "__JOBDONE..."` ← Remover!

## Deveria ser apenas

```
Triângulos são figuras 2D e não têm volume - eles têm área.
A fórmula para calcular a área de um triângulo é:
**Área = (base × altura) ÷ 2**
Se você está perguntando sobre um volume, talvez esteja se referindo a um prisma
triangular ou pirâmide triangular.
```

## Solução

Melhorar o filtro para remover:
1. Linhas contendo caminho de binário (`/bin/opencode`, `.venv/bin/`)
2. Linhas com `SENTINEL_PREFIX` (`__JOBDONE_`)
3. Linhas com comandos (prompt)
4. Linhas vazias

## Código atual

```python
for line in captured.split('\n'):
    line = line.rstrip()
    if not line or SENTINEL_PREFIX in line:
        continue
    if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@', '/']):
        continue
    lines.append(line)
```

## Problema com o filtro atual

O comando `opencode run ...` não começa com `$` ou `>`, então passa pelo filtro.

## Melhoria necessária

```python
for line in captured.split('\n'):
    line = line.rstrip()
    # Remover linhas vazias
    if not line:
        continue
    # Remover sentinela
    if SENTINEL_PREFIX in line:
        continue
    # Remover linhas com caminho de binário
    if '/bin/opencode' in line or '/opencode run' in line:
        continue
    # Remover comandos (prompt)
    if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@']):
        continue
    # Remover linhas que parecem comandos (contêm "run" no início)
    if line.strip().startswith('opencode run'):
        continue
    lines.append(line)
```

## Status

⏳ **Precisa melhorar o filtro**
