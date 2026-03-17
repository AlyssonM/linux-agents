# Fazer Attach em Sessão tmux (job)

## Sessão ativa
```bash
job-c41038e2: 1 windows (created Tue Mar 17 02:27:35 2026)
```

## 1. Fazer Attach (entrar na sessão)

```bash
# Attach na sessão
tmux attach-session -t job-c41038e2

# Ou forma curta
tmux a -t job-c41038e2
```

Você verá o output do job em tempo real.

## 2. Acompanhar a execução

Dentro da sessão tmux, você pode:
- **Ver output** em tempo real
- **Scroll** para cima: `Ctrl+B` então `Page Up` (ou setas)
- **Buscar texto**: `Ctrl+B` então `[` para entrar em copy mode, então `/` para buscar
- **Sair do scroll**: `q` ou `Enter`

## 3. Sair SEM matar a sessão (Detach)

### Opção A: Detach (RECOMENDADO)
```bash
# Prefix padrão: Ctrl+B
# Pressione: Ctrl+B então D

# Ou comando
tmux detach -t job-c41038e2
```

**Resultado**: Sessão continua rodando em background!

### Opção B: Sair e matar a sessão (NÃO RECOMENDADO)
```bash
# Dentro da sessão
exit

# Ou de fora
tmux kill-session -t job-c41038e2
```

**Resultado**: Sessão e job são mortos!

## 4. Ver output SEM attach (Alternativa)

Se só quiser ver o output sem entrar na sessão:

```bash
# Capturar últimas 500 linhas
tmux capture-pane -p -t job-c41038e2 -S -500

# Capturar e salvar em arquivo
tmux capture-pane -p -t job-c41038e2 -S -1000 > /tmp/job-c41038e2.log

# Ver em tempo real (como tail -f)
watch -n 1 'tmux capture-pane -p -t job-c41038e2 -S -10 | tail -20'
```

## 5. Listar todas as sessões de jobs

```bash
# Ver todas as sessões tmux
tmux ls

# Filtrar apenas jobs
tmux ls | grep job-
```

## 6. Workflow completo

### Fluxo normal
```bash
# 1. Ver se a sessão existe
tmux ls | grep job-c41038e2

# 2. Attach para acompanhar
tmux a -t job-c41038e2

# 3. Acompanhar output em tempo real
# (só observar)

# 4. Sair sem matar (Ctrl+B então D)
# Sessão continua rodando
```

### Fluxo alternativo (sem attach)
```bash
# Ver output sem entrar na sessão
tmux capture-pane -p -t job-c41038e2 -S -50 | tail -30

# Ou monitorar continuamente
watch -n 2 'tmux capture-pane -p -t job-c41038e2 -S -10'
```

## 7. Atalhos úteis do tmux

Dentro da sessão (depois de `Ctrl+B`):

| Atalho | Ação |
|--------|------|
| `D` | Detach (sair sem matar) |
| `[` | Entrar em copy mode (scroll) |
| `Page Up` | Scroll para cima (no copy mode) |
| `q` | Sair do copy mode |
| `d` | Detach cliente atual |

## 8. Múltiplos jobs ao mesmo tempo

```bash
# Ver todos os jobs
tmux ls | grep job-

# Attach em um específico
tmux a -t job-c41038e2

# Ver output de vários (sem attach)
for job in $(tmux ls | grep job- | cut -d: -f1); do
  echo "=== $job ==="
  tmux capture-pane -p -t "$job" -S -5 | tail -10
done
```

## 9. Troubleshooting

### Sessão não existe mais
```bash
tmux a -t job-c41038e2
# error: session not found

# Significa que o job terminou e a sessão foi morta
```

### Não consegue fazer attach (já está attachada)
```bash
# Matar sessão zumbi
tmux kill-session -t job-c41038e2
```

### Ver log do job (alternative)
```bash
# O worker salva status no YAML
cat ~/Github/linux-agents/listen/jobs/c41038e2.yaml
```

## 10. Integração com listen

O worker do listen automaticamente:
1. Cria sessão `job-<ID>`
2. Roda o job na sessão
3. Captura output
4. Mata a sessão ao terminar

**Você normalmente NÃO precisa fazer attach**, mas pode se quiser acompanhar em tempo real!

## Resumo rápido

```bash
# Attach (entrar)
tmux a -t job-c41038e2

# Detach (sair sem matar)
# Ctrl+B então D

# Ver output sem entrar
tmux capture-pane -p -t job-c41038e2 -S -50 | tail -20

# Matar sessão
tmux kill-session -t job-c41038e2
```
