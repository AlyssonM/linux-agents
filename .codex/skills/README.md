---
name: skills-documentation
description: Documentation for available Linux Agents skills and automation tools.
---

# Linux Agents Skills

Skills para automação em Linux (Raspberry Pi 4 ARM64), equivalentes às skills do Mac Mini Agent adaptadas para Linux.

## Skills Disponíveis

### rpi-gui (GUI Automation)
**Similar ao:** `steer` (macOS)

Automatização de interface gráfica Linux via pyatspi, xdotool e Tesseract OCR.

**Localização:** `linux-agents/rpi-gui/`

**Comandos principais:**
- `see` - Captura screenshot + árvore de acessibilidade
- `click` - Clica em elementos ou coordenadas
- `type` - Digita texto
- `ocr` - Reconhecimento de texto via Tesseract
- `screenshot` - Captura tela (grim/scrot)

**Requisitos:**
- X11 (DISPLAY=:1) para type/click
- Wayland (DISPLAY=:0) apenas para screenshots

**Documentação:** [rpi-gui/SKILL.md](rpi-gui/SKILL.md)

---

### rpi-term (Terminal Automation)
**Similar ao:** `drive` (macOS)

Automação de terminal via tmux com orquestração de sessões e comandos.

**Localização:** `linux-agents/rpi-term/`

**Comandos principais:**
- `session create` - Cria sessão tmux
- `run` - Executa comando e aguarda conclusão
- `send` - Envia keystrokes (sem aguardar)
- `logs` - Captura output do pane
- `poll` - Aguarda por padrão no output
- `fanout` - Executa em paralelo across sessões
- `proc` - Gerenciamento de processos

**Protocolo Sentinel:**
```bash
__START_<token>
<command output>
__DONE_<token>:<exit_code>
```

**Documentação:** [rpi-term/SKILL.md](rpi-term/SKILL.md)

---

### rpi-job (Job Server)
**Similar ao:** `listen` (macOS)

Servidor FastAPI para submissão de jobs assíncronos.

**Localização:** `linux-agents/rpi-job/`

**Endpoints:**
- `POST /job` - Submete novo job
- `GET /job/{id}` - Consulta status
- `GET /jobs` - Lista todos os jobs
- `POST /job/{id}/stop` - Para job em execução
- `POST /jobs/clear` - Arquiva jobs completados

**Porta padrão:** 7600

**Armazenamento:** Arquivos YAML em `jobs/`

**Worker:** Executa comandos shell via subprocess (sem LLM por padrão)

**Documentação:** [rpi-job/SKILL.md](rpi-job/SKILL.md)

---

### rpi-client (Job Client)
**Similar ao:** `direct` (macOS)

CLI client para interagir com rpi-job server.

**Localização:** `linux-agents/rpi-client/`

**Comandos principais:**
- `start` - Submete job
- `status` - Consulta status
- `list` - Lista jobs
- `stop` - Para job
- `clear` - Arquiva jobs
- `logs` - Stream logs (experimental)

**Uso típico:**
```bash
rpi-client start http://localhost:7600 "ls -la" --json
```

**Documentação:** [rpi-client/SKILL.md](rpi-client/SKILL.md)

---

### secretctl (Secure Secret Management)

Gerenciamento seguro de secrets (senhas, API keys, tokens) via Linux kernel keyring (keyctl). Secrets nunca são expostos a logs, histórico de sessão ou listagem de processos.

**Localização:** `linux-agents/.codex/skills/secretctl/`

**Comandos principais:**
- `set` - Armazena um secret no keyring do kernel
- `get` - Recupera secret (apenas para pipe - nunca expõe valor)
- `delete` - Remove secret
- `list` - Lista identificadores (sem valores)
- `exists` - Verifica se secret existe
- `update` - Atualiza valor ou TTL

**Segurança:**
- Armazenamento no keyring do kernel Linux (não em disco)
- Valores nunca aparecem em logs ou histórico shell
- Suporte a TTL para auto-expiração
- Isolamento por namespace de usuário

**Documentação:** [secretctl/SKILL.md](secretctl/SKILL.md)

---

## Diferenças Principais vs macOS

| Aspecto | macOS (Mac Mini Agent) | Linux (Linux Agents) |
|---------|------------------------|----------------------|
| **GUI** | Swift + AppKit + Vision | Python + pyatspi + xdotool + Tesseract |
| **Terminal** | tmux (igual) | tmux (igual) |
| **Display** | macOS displays | X11 (tightvnc :1) ou Wayland (wayvnc :0) |
| **OCR** | Vision framework | Tesseract |
| **Clipboard** | NSPasteboard | xclip |
| **Process** | macOS Activity Monitor | Linux /proc filesystem |
| **Server** | Custom (macOS) | FastAPI (cross-platform) |

---

## Instalação

```bash
cd linux-agents

# rpi-term
cd rpi-term && pip install -e .

# rpi-gui
cd rpi-gui && pip install -e .

# rpi-job
cd rpi-job && pip install -e .

# rpi-client
cd rpi-client && pip install -e .
```

---

## Uso Rápido

### Terminal Automation
```bash
# Criar sessão
rpi-term session create test --json

# Executar comando
rpi-term run test "ls -la" --json

# Enviar keystrokes
rpi-term send test "vim file.txt" --json

# Capturar logs
rpi-term logs test --json
```

### GUI Automation
```bash
# Ver tela
rpi-gui see --screen 0 --json

# Clicar em elemento
rpi-gui click --id B1 --json

# Digitar texto
rpi-gui type "Hello World" --json

# OCR
rpi-gui ocr --store --json
```

### Job Server
```bash
# Iniciar servidor
cd linux-agents/rpi-job && rpi-job

# Submeter job
rpi-client start http://localhost:7600 "ls -la" --json

# Consultar status
rpi-client status http://localhost:7600 <job_id> --json
```

---

## Integração com Agentes de IA

Estas skills são **agnósticas ao modelo** e podem ser usadas por qualquer agente:

- GPT-4
- Claude
- Gemini
- Codex
- Qualquer outro modelo

O agente apenas precisa chamar os comandos das skills (rpi-gui, rpi-term, rpi-job, rpi-client) para executar automação.

---

## Documentação Complementar

- [E2E Test Results](../specs/README.md)
- [Technical Architecture](../obsidian-vault/linux-agents/Technical%20Architecture.md)
- [Applications and Use Cases](../obsidian-vault/linux-agents/Applications%20and%20Use%20Cases.md)

---

## Referências

Baseado no [Mac Mini Agent](https://github.com/disler/mac-mini-agent) por [@disler](https://github.com/disler), adaptado para Linux/Raspberry Pi.

---

**Autor:** Arpie 🚀
**Data:** 2026-03-16
**Versão:** 1.0.0
