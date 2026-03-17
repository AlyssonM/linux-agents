import { spawn } from 'node:child_process';
import process from 'node:process';
import { Readable, Writable } from 'node:stream';

import { ClientSideConnection, PROTOCOL_VERSION } from 'file:///home/alyssonpi/.npm-global/lib/node_modules/openclaw/node_modules/@agentclientprotocol/sdk/dist/acp.js';

const OPENCLAW_ENTRY = '/home/alyssonpi/.npm-global/lib/node_modules/openclaw/openclaw.mjs';
const MAX_IGNORED_LINES = 50;
const DEFAULT_INIT_TIMEOUT_MS = 30000;
const DEFAULT_ATTEMPTS = 3;
const RETRYABLE_PATTERNS = [
  /gateway closed before ready/i,
  /gateway connect failed/i,
  /timed out/i,
  /econnreset/i,
  /socket hang up/i,
];

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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createFilteredNdjsonStream(output, input, onIgnoredLine, onWriteError) {
  const textEncoder = new TextEncoder();
  const textDecoder = new TextDecoder();

  const readable = new ReadableStream({
    async start(controller) {
      let content = '';
      const reader = input.getReader();
      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          if (!value) continue;
          content += textDecoder.decode(value, { stream: true });
          const lines = content.split('\n');
          content = lines.pop() || '';
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            const first = trimmed[0];
            if (first !== '{' && first !== '[') {
              onIgnoredLine?.(trimmed);
              continue;
            }
            try {
              controller.enqueue(JSON.parse(trimmed));
            } catch {
              onIgnoredLine?.(trimmed);
            }
          }
        }
      } finally {
        reader.releaseLock();
        controller.close();
      }
    },
  });

  const writable = new WritableStream({
    async write(message) {
      const writer = output.getWriter();
      try {
        await writer.write(textEncoder.encode(`${JSON.stringify(message)}\n`));
      } catch (err) {
        onWriteError?.(err);
        throw err;
      } finally {
        writer.releaseLock();
      }
    },
  });

  return { readable, writable };
}

function withTimeout(promise, ms, label) {
  if (!ms || !Number.isFinite(ms) || ms <= 0) return promise;
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      const id = setTimeout(() => {
        clearTimeout(id);
        reject(new Error(`${label} timed out after ${ms}ms`));
      }, ms);
    }),
  ]);
}

function isRetryableError(text) {
  return RETRYABLE_PATTERNS.some((pattern) => pattern.test(text || ''));
}

function summarizeIgnoredLines(lines) {
  return lines.slice(0, MAX_IGNORED_LINES);
}

function buildMessage(messageOrder, messageChunksById) {
  return messageOrder
    .map((id) => (messageChunksById.get(id) || []).join(''))
    .join('\n\n')
    .trim();
}

async function runAttempt({ cwd, instruction, sessionKey, timeoutMs, thinking, attempt }) {
  const child = spawn(process.execPath, [OPENCLAW_ENTRY, 'acp', '--session', sessionKey, '--reset-session'], {
    cwd,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: {
      ...process.env,
      OPENCLAW_SHELL: 'openclaw-listen-acp-runner',
    },
  });

  if (!child.stdin || !child.stdout || !child.stderr) {
    throw new Error('failed to open ACP stdio pipes');
  }

  const ignoredStdoutLines = [];
  const stderrChunks = [];
  const messageChunksById = new Map();
  const messageOrder = [];
  let toolEvents = 0;
  const updates = [];
  let writeError = null;

  child.stderr.on('data', (chunk) => {
    stderrChunks.push(String(chunk));
  });

  const stream = createFilteredNdjsonStream(
    Writable.toWeb(child.stdin),
    Readable.toWeb(child.stdout),
    (line) => {
      if (ignoredStdoutLines.length < MAX_IGNORED_LINES) ignoredStdoutLines.push(line);
    },
    (err) => {
      writeError = err instanceof Error ? err.message : String(err);
    },
  );

  const client = new ClientSideConnection(() => ({
    sessionUpdate: async (params) => {
      const update = params?.update;
      if (!update) return;

      if (update.sessionUpdate === 'agent_message_chunk') {
        const content = update.content;
        if (content?.type === 'text' && typeof content.text === 'string') {
          const messageId = update.messageId || 'default';
          if (!messageChunksById.has(messageId)) {
            messageChunksById.set(messageId, []);
            messageOrder.push(messageId);
          }
          messageChunksById.get(messageId).push(content.text);
        }
        return;
      }

      if (update.sessionUpdate === 'tool_call' || update.sessionUpdate === 'tool_call_update') {
        toolEvents += 1;
        return;
      }

      if (
        update.sessionUpdate === 'session_info_update' ||
        update.sessionUpdate === 'usage_update' ||
        update.sessionUpdate === 'available_commands_update' ||
        update.sessionUpdate === 'current_mode_update' ||
        update.sessionUpdate === 'config_option_update'
      ) {
        updates.push(update.sessionUpdate);
      }
    },
    requestPermission: async (params) => {
      const option = (params?.options || []).find((opt) => opt.kind === 'allow_once' || opt.kind === 'allow_always') || params?.options?.[0];
      if (!option) return { outcome: { outcome: 'cancelled' } };
      return { outcome: { outcome: 'selected', optionId: option.optionId } };
    },
  }), stream);

  try {
    await withTimeout(
      client.initialize({
        protocolVersion: PROTOCOL_VERSION,
        clientCapabilities: {
          fs: { readTextFile: true, writeTextFile: true },
          terminal: true,
        },
        clientInfo: { name: 'openclaw-listen-acp-runner', version: '0.3.0' },
      }),
      Math.min(timeoutMs || DEFAULT_INIT_TIMEOUT_MS, DEFAULT_INIT_TIMEOUT_MS),
      'ACP initialize',
    );

    const { sessionId } = await withTimeout(
      client.newSession({
        cwd,
        mcpServers: [],
        _meta: {
          sessionKey,
          resetSession: true,
          prefixCwd: false,
        },
      }),
      Math.min(timeoutMs || DEFAULT_INIT_TIMEOUT_MS, DEFAULT_INIT_TIMEOUT_MS),
      'ACP newSession',
    );

    const response = await withTimeout(
      client.prompt({
        sessionId,
        prompt: [{ type: 'text', text: instruction }],
        _meta: {
          timeoutMs,
          thinking,
          prefixCwd: false,
        },
      }),
      timeoutMs,
      'ACP prompt',
    );

    const stderrText = stderrChunks.join('').trim();
    return {
      ok: true,
      attempt,
      sessionKey,
      sessionId,
      stopReason: response?.stopReason || null,
      userMessageId: response?.userMessageId || null,
      message: buildMessage(messageOrder, messageChunksById),
      toolEvents,
      updates,
      ignoredStdoutLines: summarizeIgnoredLines(ignoredStdoutLines),
      stderr: stderrText ? stderrText.slice(0, 4000) : '',
      writeError,
      messageIds: messageOrder,
    };
  } catch (err) {
    const stderrText = stderrChunks.join('').trim();
    const errorMessage = err instanceof Error ? err.message : String(err);
    return {
      ok: false,
      attempt,
      error: errorMessage,
      sessionKey,
      ignoredStdoutLines: summarizeIgnoredLines(ignoredStdoutLines),
      stderr: stderrText ? stderrText.slice(0, 4000) : '',
      writeError,
      partialMessage: buildMessage(messageOrder, messageChunksById),
      messageIds: messageOrder,
    };
  } finally {
    child.kill();
  }
}

const args = parseArgs(process.argv);
const instruction = args.instruction || '';
const cwd = args.cwd || process.cwd();
const sessionKey = args['session-key'] || `agent:listen-v2:job:${Date.now()}`;
const timeoutMs = args['timeout-ms'] ? Number(args['timeout-ms']) : undefined;
const thinking = args.thinking || undefined;
const attempts = args.attempts ? Math.max(1, Number(args.attempts)) : DEFAULT_ATTEMPTS;

if (!instruction.trim()) {
  console.error(JSON.stringify({ ok: false, error: 'instruction is required' }));
  process.exit(2);
}

let lastResult = null;
for (let attempt = 1; attempt <= attempts; attempt += 1) {
  const result = await runAttempt({ cwd, instruction, sessionKey, timeoutMs, thinking, attempt });
  if (result.ok) {
    console.log(JSON.stringify(result));
    process.exit(0);
  }

  lastResult = result;
  const retryText = [result.error, result.stderr, result.writeError].filter(Boolean).join('\n');
  const shouldRetry = attempt < attempts && isRetryableError(retryText);
  if (!shouldRetry) break;
  await sleep(1000 * attempt);
}

console.error(JSON.stringify(lastResult || { ok: false, error: 'unknown ACP runner failure', sessionKey }));
process.exit(1);
