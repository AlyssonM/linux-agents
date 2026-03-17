# Multi-Agent Support

The `/job` endpoint supports multiple AI agents via the `agent` parameter.

## Available Agents

### 1. **codex** (Original, Limited)
- **Implementation:** Uses `codex exec` with prompt templates
- **Status:** ⚠️ **OpenAI API limit reset** (until Mar 18, 2026)
- **When to use:** After API limit resets
- **Model support:** ✅ Yes (`--model` parameter)
- **Prompts:** Uses `.opencode/agents/job-system-prompt.md`

### 2. **claude** (Alias)
- **Implementation:** Maps to `opencode` for now
- **Status:** ✅ **Available**
- **When to use:** Alternative name for opencode
- **Model support:** ✅ Yes (via opencode)
- **Note:** Compatibility alias

### 3. **opencode** (Available) ✅ **RECOMMENDED**
- **Implementation:** Uses `~/.opencode/bin/opencode run`
- **Status:** ✅ **Available and working**
- **When to use:** Default choice when codex is limited
- **Model support:** ❌ Not yet (TODO in code)
- **Binary:** `~/.opencode/bin/opencode`

## Removed Agents

### **openclaw** (Removed)
- **Reason:** Dedicated `openclaw-listen` server exists (port 7610)
- **Location:** `~/Github/linux-agents/openclaw-listen/`
- **Use instead:** Use `openclaw-listen` for OpenClaw agent execution

## Usage Examples

### Using opencode (recommended)
```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Listar arquivos em ~/Downloads/",
    "agent": "opencode"
  }'
```

### Using codex (after API reset)
```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Abrir Chromium e navegar para example.com",
    "agent": "codex"
  }'
```

### With custom model (codex only)
```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "minha tarefa",
    "agent": "codex",
    "model": "gpt-4o"
  }'
```

## Agent Comparison

| Agent | Available | Model Support | Prompts | Status |
|-------|-----------|---------------|---------|--------|
| **codex** | ⚠️ API limited | ✅ | `.opencode/agents/` | Original |
| **claude** | ✅ (via opencode) | ✅ | Native | Alias |
| **opencode** | ✅ Yes | ❌ TODO | Native | **Recommended** |

## Alternative: openclaw-listen

For OpenClaw-specific agent execution, use the dedicated server:

```bash
# Start openclaw-listen (port 7610)
cd ~/Github/linux-agents/openclaw-listen
python main.py

# Use it
curl -X POST http://localhost:7610/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "minha tarefa"}'
```

## Implementation Details

See `worker.py` for the implementation:
- `_run_codex()` - Original tmux + codex exec
- `_run_opencode()` - OpenCode binary

## Future Work

1. **Add model support to opencode** - Currently TODO in code
2. **Unified prompt system** - Share templates between agents
