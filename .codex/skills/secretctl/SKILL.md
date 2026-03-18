---
name: secretctl
description: Secure secret management CLI for AI agents. Use secretctl to store, retrieve, and manage passwords, API keys, tokens without exposing them to AI conversations. MCP integration, AES-256-GCM encryption, output sanitization. Never leak secrets to logs or session history.
---

# secretctl — AI-Safe Secret Management

**Tool:** [forest6511/secretctl](https://github.com/forest6511/secretctl)
**Type:** Single-binary CLI with MCP integration
**Security:** AES-256-GCM + Argon2id + output sanitization

Run `secretctl <command> --help` to learn each command's flags.

## Setup Inicial (secretctl + pass)

### 1) Pré-requisitos

```bash
sudo apt update
sudo apt install -y gnupg2 pass
```

### 2) Criar chave GPG (se ainda não existir)

```bash
gpg --full-generate-key
gpg --list-secret-keys --keyid-format LONG
```

Use o `KEYID` retornado no próximo comando.

### 3) Inicializar o pass

```bash
pass init <KEYID>
```

### 4) Inicializar o secretctl

```bash
secretctl init
```

### 5) Salvar a master password no pass

```bash
pass insert -f secretctl/master-password
pass show secretctl/master-password
```

### 6) Validar o fluxo local

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" secretctl list
```

### 7) Permissões recomendadas de policy MCP

```bash
chmod 700 ~/.secretctl
chmod 600 ~/.secretctl/mcp-policy.yaml
```

### 8) Cache de senha GPG (opcional)

Em `~/.gnupg/gpg-agent.conf`:

```conf
default-cache-ttl 28800
max-cache-ttl 86400
```

Depois recarregue:

```bash
gpgconf --kill gpg-agent
```

## Uso Sem MCP (Agêntico e Seguro)

Quando o agente não tiver MCP, use `secretctl run` com senha obtida de cofre local, sem hardcode.

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
  secretctl run -k OPENROUTER_API_KEY -- \
  env | grep OPENROUTER
```

Fluxo recomendado para agentes (Ambiente sem TTY):

Ambiente sem TTY (usando script que acompanha a skill em `skills/secretctl/scripts`):

```bash
SKILL_DIR="${HOME}/.pi/skills/secretctl"
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
  python3 "${SKILL_DIR}/scripts/wrapper_secretctl.py" run -k OPENROUTER_API_KEY -- \
  python3 test_openrouter.py
```

Regras obrigatórias no modo sem MCP:
- Nunca usar senha literal em scripts, JSON, markdown ou histórico
- Nunca exportar segredo de API em texto claro
- Preferir `SECRETCTL_PASSWORD="$(pass show ...)" comando` em linha única

## Agentic MCP Setup

Use `mcp-server` so the LLM can run commands with secrets without seeing plaintext values.

`SECRETCTL_PASSWORD` is read once and cleared by `secretctl` on startup.

Do not store master password directly in JSON config files.

### Codex (`.codex/config.toml`)

```toml
[mcp_servers.secretctl]
command = "/usr/bin/env"
args = [
  "bash",
  "-lc",
  "SECRETCTL_PASSWORD=\"$(pass show secretctl/master-password)\" exec /usr/local/bin/secretctl mcp-server"
]
startup_timeout_sec = 20
tool_timeout_sec = 60
enabled = true
```

Validação:

```bash
codex mcp list
```

Safer Claude Code style MCP config (without plaintext password in JSON):

```json
{
  "mcpServers": {
    "secretctl": {
      "type": "stdio",
      "command": "/usr/bin/env",
      "args": [
        "bash",
        "-lc",
        "SECRETCTL_PASSWORD=\"$(pass show secretctl/master-password)\" exec /usr/local/bin/secretctl mcp-server"
      ]
    }
  }
}
```

Alternative flow (still safe, no plaintext hardcode):

```bash
export SECRETCTL_PASSWORD="$(pass show secretctl/master-password)"
claude
unset SECRETCTL_PASSWORD
```

Create `~/.secretctl/mcp-policy.yaml` to allow only safe commands in `secret_run`.
Without policy, `secret_run` is denied by default.

## Commands

### set — Store a secret

```bash
secretctl set OPENAI_API_KEY
secretctl set GITHUB_TOKEN
secretctl set DB_PASSWORD --expires 30d --tags prod,db
secretctl set APP_DB --template database --field username=admin --field password=secret
```

**Security Notes:**
- For sensitive values, prefer interactive input (`secretctl set KEY`) to avoid shell history
- Stored with AES-256-GCM encryption
- Optional metadata: `--notes`, `--tags`, `--url`, `--expires`
- `--field` puts values in command arguments, so avoid it for highly sensitive plaintext

### get — Retrieve a secret

```bash
secretctl get OPENAI_API_KEY
secretctl get DB_PASSWORD --show-metadata
```

**Security Notes:**
- Returns raw secret value for piping only
- NEVER echo back result - always pipe to consuming command

### list — List secrets

```bash
secretctl list
secretctl list --tag=prod
secretctl list --expiring=7d
```

### delete — Remove a secret

```bash
secretctl delete OPENAI_API_KEY
```

### run — Execute commands with injected secrets

```bash
secretctl run -k AWS_ACCESS_KEY_ID -- aws s3 ls
secretctl run -k "aws/*" -- aws s3 ls
secretctl run -k DB_PASSWORD -- ./deploy.sh
```

**Flags:**
- `-k, --key`: Secret key pattern to inject (supports wildcards like `aws/*`)
- `--timeout`: Command timeout (e.g., `30s`)
- `--env-prefix`: Prefix for injected env vars

**Output Sanitization:**
If the command outputs a secret value, it appears as `[REDACTED:KEY_NAME]`.

## Security Model

| Feature | Protection |
|---------|------------|
| **AES-256-GCM** | Encryption at rest |
| **Argon2id** | Brute-force resistant key derivation |
| **Interactive input** | Avoids secrets in shell history/arguments |
| **Output sanitization** | Redacts secrets if printed |
| **MCP integration** | Direct Claude Code integration |
| **Local-first** | No cloud, no third-party servers |

## Security Rules

1. **Prefer interactive set** — Use `secretctl set KEY` and type value when prompted
2. **Use `run` for commands** — It injects secrets as env vars automatically
3. **Check output** — If you see `[REDACTED:...]`, sanitization is working
4. **Use patterns for multiple secrets** — `secretctl run -k "aws/*" -- aws ...`
5. **Set metadata** — Add `--tags` and `--expires` for organization
6. **Use MCP policy** — Allow-list commands for `secret_run` with deny-by-default

## Examples

**AI-safe API call:**
```bash
secretctl run -k OPENAI_API_KEY -- curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**Git operations:**
```bash
secretctl set GH_TOKEN
secretctl run -k GH_TOKEN -- git push origin main
```

**Database deployment:**
```bash
secretctl set DB_PASSWORD
secretctl run -k DB_PASSWORD --timeout=60s -- ./migrate.sh
```

**Pattern matching for AWS:**
```bash
secretctl set aws/access_key
secretctl set aws/secret_key
secretctl run -k "aws/*" -- aws ec2 describe-instances
```
