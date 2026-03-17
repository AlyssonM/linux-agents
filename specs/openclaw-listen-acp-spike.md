# Spike técnico — `openclaw-listen` v2 baseado em ACP

## Objetivo
Descobrir se `openclaw acp` / `openclaw acp client` pode ser usado de forma **scriptável por shell** para executar prompts **one-shot** com **session key isolada por job**, ou se o v2 precisa integrar o protocolo ACP de outro jeito.

## Resposta curta
**Sim, é viável usar ACP no v2, mas não do jeito “shell puro usando `openclaw acp client`”.**

- `openclaw acp` é um **servidor ACP via stdio** que faz bridge para o Gateway.
- `openclaw acp client` é apenas um **cliente interativo de terminal**; não é uma API one-shot pronta para automação de shell.
- Para um executor v2 robusto com **sessão isolada por job**, o caminho correto hoje é:
  1. gerar uma **session key dedicada** por job;
  2. iniciar um processo `openclaw acp --session <job-session-key> --reset-session`;
  3. falar com esse processo via **ACP JSON-RPC/NDJSON em stdio** usando SDK ACP ou um cliente próprio;
  4. enviar `session/new` ou `session/load`, depois `prompt`, e encerrar o processo ao fim.

Em outras palavras: **ACP serve**, mas o v2 deve integrar o **protocolo ACP** diretamente; **não** depender de `openclaw acp client` como interface de automação.

---

## O que a documentação/código local mostra

### 1) `openclaw acp` é um bridge ACP real
No dist local do OpenClaw (`dist/acp-cli-*.js`):

- comando registrado como:
  - `openclaw acp` → “Run an ACP bridge backed by the Gateway”
- opções relevantes:
  - `--session <key>`
  - `--session-label <label>`
  - `--require-existing`
  - `--reset-session`
  - `--provenance`

Também há lógica explícita para:
- resolver session key/label via Gateway (`sessions.resolve`)
- resetar sessão (`sessions.reset`)
- enviar prompt via `chat.send`
- alterar config de sessão via `sessions.patch`
- carregar transcript via `sessions.get`

### 2) `openclaw acp client` é interativo, não one-shot
O CLI registra:
- `openclaw acp client` → “Run an interactive ACP client against the local ACP bridge”

Ou seja, ele é um utilitário humano/TTY para conversar com um servidor ACP local. Não apareceu nenhum modo do tipo:
- `--prompt ...`
- `--json`
- `--session ... --once`
- `stdin -> resposta final -> exit`

Pelo código, ele chama `runAcpClientInteractive(...)`, reforçando que o foco é REPL/terminal interativo.

### 3) O bridge ACP suporta exatamente o que o v2 precisa
No código local do bridge ACP:

- `resolveSessionKey(...)`
  - aceita session key ou label
  - permite `requireExisting`
  - se `requireExisting=false`, aceita uma key arbitrária
- `resetSessionIfNeeded(...)`
  - chama `sessions.reset`
- `prompt(...)`
  - converte prompt ACP em `chat.send` no Gateway
  - usa `idempotencyKey` por run
  - recebe stream/deltas/final via eventos do Gateway
- `loadSession(...)`
  - reidrata transcript do Gateway
- `setSessionConfigOption(...)`
  - muda thinking/fast/verbose/reasoning/responseUsage/elevatedLevel via `sessions.patch`

Tradução prática: o bridge já oferece o encaixe para um executor por job com sessão dedicada.

---

## Experimentos seguros feitos

### `openclaw acp --help`
Confirmou as opções acima, especialmente `--session` e `--reset-session`.

### `openclaw acp client --help`
Confirmou que o cliente exposto hoje é interativo.

### Smoke test de stdio
Tentei subir `openclaw acp` e mandar um `initialize` mínimo por stdio. O teste não virou um fluxo fim-a-fim confiável porque o processo fechou cedo com erro de conexão/ready do gateway, mas serviu para confirmar o ponto arquitetural importante:

- `openclaw acp` é um processo pensado para ser dirigido por **stdio/protocolo**;
- o problema observado foi de handshake/estado do bridge, não de ausência de interface ACP.

Esse teste foi mantido propositalmente superficial para evitar acionar conversas reais ou jobs com efeitos colaterais.

---

## O que é viável hoje

## Viável

### Opção A — integrar ACP diretamente no v2
**Recomendado.**

Fluxo por job:
1. gerar `job_id`
2. derivar `session_key = agent:listen-v2:job:<job_id>` (ou outro namespace estável)
3. spawnar:
   ```bash
   openclaw acp --session "$session_key" --reset-session
   ```
4. via ACP stdio:
   - `initialize`
   - `session/new` ou `session/load`
   - `prompt`
   - consumir deltas/tool calls/final
5. persistir resultado no estado do `openclaw-listen`
6. encerrar processo ACP

Benefícios:
- isolamento real por job
- reaproveita roteamento/sessão/histórico/config do Gateway
- sem precisar implementar `chat.send`/streaming na unha
- pode usar `--provenance meta+receipt` se quiser rastreabilidade melhor

### Opção B — bypass do ACP e falar direto com Gateway
**Viável, mas menos alinhado ao objetivo do v2.**

Se o foco fosse só one-shot, daria para chamar o Gateway direto (algo análogo ao que o bridge faz com `chat.send`, `sessions.reset`, `sessions.patch`).

Mas isso força o v2 a reimplementar:
- handshake/conexão
- streaming de eventos
- normalização de sessão
- parte do comportamento que o ACP bridge já encapsula

Então eu só escolheria isso se houver requisito forte de eliminar o processo filho `openclaw acp`.

## Não viável / não recomendado

### Usar `openclaw acp client` como automação de shell do v2
Não parece ser o caminho certo.

Motivos:
- é **interativo**, não uma CLI one-shot estável
- não expõe flags de prompt/output estruturado para scripting
- automatizar um REPL com `expect`, pipes cegos ou pseudo-TTY seria frágil

Resumo sincero: **dá para gambiarrear**, mas seria engenharia de sofrimento.

---

## Proposta concreta de design para `openclaw-listen` v2

## Arquitetura recomendada

### Componente novo: ACP Runner
Criar um módulo dedicado, algo como:
- `OpenClawAcpRunner`
- `AcpJobExecutor`

Responsabilidades:
- spawn do processo `openclaw acp`
- handshake ACP via stdio
- criação/carregamento de sessão
- envio do prompt do job
- coleta de eventos/deltas/tool calls
- timeout/cancelamento
- teardown limpo do processo

### Session key por job
Formato sugerido:
```text
agent:listen-v2:job:<uuid>
```

ou, se quiser particionar por fila/origem:
```text
agent:listen-v2:<queue>:<job-id>
```

Regras:
- **uma session key por job**
- usar `--reset-session` sempre para garantir isolamento sem depender de cleanup posterior
- nunca reutilizar session key entre jobs distintos

### Transporte
Usar stdio com cliente ACP programático, de preferência via SDK ACP já usado pelo OpenClaw (`@agentclientprotocol/sdk` aparece no código local).

### Fluxo recomendado
1. `spawn(openclaw acp --session <key> --reset-session [--provenance meta+receipt])`
2. `initialize`
3. `session/new` com `cwd` do job
4. opcionalmente `setSessionConfigOption` / `setSessionMode`
5. `prompt` com o texto do job
6. stream de saída até final
7. fechar processo

### Timeouts e cancelamento
- timeout do job no runner
- se cancelar:
  - enviar `cancel`/abort via ACP
  - matar processo ACP se necessário

### Observabilidade
Persistir por job:
- `session_key`
- `run_id` / idempotency key, se exposto
- timestamps
- status final
- texto final
- erros
- resumo de tool calls (se útil)

### Concorrência
Modelo simples e saudável:
- **1 processo `openclaw acp` por job**
- isolamento total de stdio/estado do cliente
- sem multiplexar várias execuções num mesmo bridge

Isso custa um pouco mais de processo, mas reduz muito a complexidade operacional.

---

## Decisão recomendada

**Escolha para o v2:**

> Implementar um runner ACP programático que sobe `openclaw acp` por job e conversa com ele via stdio/ACP.

**Não escolher:**

> Tentar dirigir `openclaw acp client` como se fosse uma CLI one-shot de shell.

Porque hoje, pragmaticamente:
- o bridge ACP já tem as primitivas certas;
- o client interativo não foi desenhado como API de automação;
- integrar o protocolo diretamente é mais sólido e menos improvisado.

---

## Próximos passos sugeridos

1. criar um micro-protótipo fora do fluxo principal do `listen`:
   - spawn do `openclaw acp`
   - `initialize`
   - `session/new`
   - `prompt("say pong and stop")`
   - imprimir texto final
2. validar timeout/cancelamento
3. validar sessão isolada por job com duas execuções em paralelo
4. só então plugar no `openclaw-listen` v2

---

## Conclusão

O caminho correto para o v2 é **ACP direto via stdio**, usando `openclaw acp` como bridge por job.

**Resposta objetiva à pergunta original:**
- **`openclaw acp`**: sim, pode participar de uma solução scriptável
- **`openclaw acp client`**: não parece adequado como interface shell one-shot para produção
- **melhor abordagem**: integrar o **protocolo ACP** no executor v2, usando `openclaw acp` como subprocesso com **session key dedicada por job**
