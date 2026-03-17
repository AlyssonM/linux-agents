import { spawn } from 'node:child_process';
import { Readable, Writable } from 'node:stream';
import process from 'node:process';
import { ClientSideConnection, PROTOCOL_VERSION, ndJsonStream } from 'file:///home/alyssonpi/.npm-global/lib/node_modules/openclaw/node_modules/@agentclientprotocol/sdk/dist/acp.js';

const OPENCLAW_ENTRY = '/home/alyssonpi/.npm-global/lib/node_modules/openclaw/openclaw.mjs';

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const key = argv[i];
    if (!key.startsWith('--')) continue;
    const name = key.slice(2);
    const value = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : 'true';
    out[name] = value;
  }
  return out;
}

const args = parseArgs(process.argv);
const instruction = args.instruction || '';
const cwd = args.cwd || process.cwd();
const sessionKey = args['session-key'] || `agent:listen-v2:job:${Date.now()}`;
const timeoutMs = args['timeout-ms'] ? Number(args['timeout-ms']) : undefined;
const thinking = args.thinking || undefined;

if (!instruction.trim()) {
  console.error(JSON.stringify({ ok: false, error: 'instruction is required' }));
  process.exit(2);
}

const child = spawn(process.execPath, [OPENCLAW_ENTRY, 'acp', '--session', sessionKey, '--reset-session'], {
  cwd,
  stdio: ['pipe', 'pipe', 'inherit'],
  env: {
    ...process.env,
    OPENCLAW_SHELL: 'openclaw-listen-acp-runner'
  }
});

if (!child.stdin || !child.stdout) {
  console.error(JSON.stringify({ ok: false, error: 'failed to open ACP stdio pipes' }));
  process.exit(2);
}

let chunks = [];
let toolEvents = 0;
let updates = [];

const client = new ClientSideConnection(() => ({
  sessionUpdate: async (params) => {
    const update = params?.update;
    if (!update) return;
    if (update.sessionUpdate === 'agent_message_chunk' && update.content?.type === 'text' && typeof update.content.text === 'string') {
      chunks.push(update.content.text);
      return;
    }
    if (update.sessionUpdate === 'tool_call' || update.sessionUpdate === 'tool_call_update') {
      toolEvents += 1;
      return;
    }
    if (update.sessionUpdate === 'session_info_update' || update.sessionUpdate === 'usage_update' || update.sessionUpdate === 'available_commands_update') {
      updates.push(update.sessionUpdate);
    }
  },
  requestPermission: async (params) => {
    // Non-interactive server mode: auto-approve safe execution path for now.
    const option = (params?.options || []).find((opt) => opt.kind === 'allow_once' || opt.kind === 'allow_always') || params?.options?.[0];
    if (!option) return { outcome: { outcome: 'cancelled' } };
    return { outcome: { outcome: 'selected', optionId: option.optionId } };
  }
}), ndJsonStream(Writable.toWeb(child.stdin), Readable.toWeb(child.stdout)));

try {
  await client.initialize({
    protocolVersion: PROTOCOL_VERSION,
    clientCapabilities: {
      fs: { readTextFile: true, writeTextFile: true },
      terminal: true,
    },
    clientInfo: { name: 'openclaw-listen-acp-runner', version: '0.1.0' }
  });

  const { sessionId } = await client.newSession({
    cwd,
    mcpServers: [],
    _meta: {
      sessionKey,
      resetSession: true,
      prefixCwd: false,
    }
  });

  const response = await client.prompt({
    sessionId,
    prompt: [{ type: 'text', text: instruction }],
    _meta: {
      timeoutMs,
      thinking,
      prefixCwd: false,
    }
  });

  const message = chunks.join('').trim();
  console.log(JSON.stringify({
    ok: true,
    sessionKey,
    sessionId,
    stopReason: response?.stopReason || null,
    message,
    toolEvents,
    updates,
  }));
  child.kill();
  process.exit(0);
} catch (err) {
  const message = err instanceof Error ? err.message : String(err);
  console.error(JSON.stringify({ ok: false, error: message, sessionKey }));
  child.kill();
  process.exit(1);
}
