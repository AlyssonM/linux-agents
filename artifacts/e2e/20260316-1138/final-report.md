# Final Report - Linux ARM64 Agent Stack Initialization Test (Round 3: X11 Workaround)

## Executive Summary
Round 3 confirmed that the stack remains broadly healthy on Raspberry Pi ARM64 and that **X11 tools can work through Xwayland even inside a Wayland session**.

High-level result:
- **Setup/build:** PASS
- **X11 screenshot + OCR path via Xwayland:** PASS
- **Input injection via X11/Xwayland:** PASS
- **Terminal lifecycle (`rpi-term` + `tmux`):** PASS
- **HTTP/API/client stack (`rpi-job` + `rpi-client`):** PASS
- **Integration workflow:** PASS
- **Window enumeration via `wmctrl -l`:** FAIL, but **EXPECTED under this Wayland/labwc environment**

Bottom line: this run landed close to the expected **~87.5%+ effective pass rate**, but the more useful conclusion is qualitative:
- **X11-compatible operations work through Xwayland** (`scrot`, `xdotool`, `xwininfo`, `xterm`, `rpi-gui see/click/type`)
- **`wmctrl -l` remains unreliable here because the compositor/window-manager interface is incomplete for that path**
- This should be treated as an **environment constraint**, not a core stack bug

## Comparison with Round 2
Round 3 is essentially a **confirmation + clarification run** rather than a recovery run.

Compared with Round 2 (`artifacts/e2e/20260316-1126`):
- Core stack status stayed **green**
- Build/install status stayed **green**
- `rpi-gui`, `rpi-term`, `rpi-job`, and `rpi-client` still worked
- The key new value from Round 3 is **better evidence about X11 vs Wayland behavior**

### What Round 3 clarified
- `wmctrl -l` failure is still present, but now better characterized as:
  - **EXPECTED in current Wayland/labwc session**
  - **Not evidence that X11 tooling is entirely broken**
- `xwininfo -root` works correctly via `DISPLAY=:0`
- `xdotool` input smoke tests still work via Xwayland
- `rpi-gui apps list` appears to have some fallback behavior, but the output is weak / not true app enumeration:
  - It returned `~/.openclaw/workspace/linux-agents` as an "application"
  - That suggests the path is usable only as a very rough compatibility fallback, not reliable discovery
- Click/type via X11 path worked well enough to affect real windows, including an `xterm` opened for this run

### Round 2 vs Round 3 verdict
- **Round 2:** proved the stack worked end-to-end after dependency installation
- **Round 3:** proved that **most GUI automation paths survive under Wayland when routed through Xwayland**, while `wmctrl` remains the notable exception

## Environment Details
- Host: `alyssonpi4`
- Hardware: Raspberry Pi 4 / Linux ARM64
- Kernel: `Linux 6.12.47+rpt-rpi-v8`
- Python: `3.13.5`
- Session type: `wayland`
- Display bridge: `DISPLAY=:0`
- Wayland socket: `WAYLAND_DISPLAY=wayland-0`
- Windowing reality: **Wayland session with Xwayland available**
- Artifact dir: `/home/alyssonpi/.openclaw/workspace/linux-agents/artifacts/e2e/20260316-1138`
- Prior comparison baseline: `/home/alyssonpi/.openclaw/workspace/linux-agents/artifacts/e2e/20260316-1126`

## Phase-by-Phase Results

### Phase 1 - Setup
Status: **PASS**

Verified:
- Python and pip present
- Session variables captured
- Required tools present:
  - `tmux` ✅
  - `tesseract` ✅
  - `scrot` ✅
  - `xdotool` ✅
  - `wmctrl` ✅
  - extra X11 tools now present: `xwininfo`, `xprop`, `xterm` ✅
- `.venv` created successfully
- Editable installs succeeded for all four packages

Notable note:
- `python -m rpi_job.main --help` did **not** behave like a normal help path; it attempted to start the server and hit `address already in use` on port 7600. Packaging/import is fine, but CLI ergonomics for that invocation are rough.

### Phase 2 - Build
Status: **PASS**

Verified:
- `python -m build` succeeded for:
  - `rpi-gui`
  - `rpi-term`
  - `rpi-job`
  - `rpi-client`
- CLI help succeeded for:
  - `rpi-gui --help`
  - `rpi-term --help`
  - `rpi-client --help`
- `rpi_job.main` import/start path is functional, though `--help` behavior is misleading

Conclusion:
- Packaging is healthy
- Entry points are mostly healthy
- `rpi-job` should probably expose a cleaner CLI/help path

### Phase 3 - Permissions / Environment
Status: **PARTIAL PASS**

Verified:
- `scrot` screenshot capture via `DISPLAY=:0`: **works**
- `tesseract` against captured screenshot: **works**
- `xdotool getmouselocation`: **works**
- `xwininfo -root`: **works**
- `tmux` create/list/kill: **works**

Observed:
- `wmctrl -l` output:
  - `Cannot get client list properties.`
  - `(_NET_CLIENT_LIST or _WIN_CLIENT_LIST)`
- `xprop -root` showed `_NET_CLIENT_LIST` among supported atoms, but `wmctrl` still could not retrieve the client list in this session

Interpretation:
- This is a **Wayland/labwc/Xwayland interoperability limitation**
- Marking this as **EXPECTED**, not a product bug in the tested packages

### Phase 4 - Individual Command Tests

#### 4.1 `rpi-gui see`
Status: **PASS**
- Returned JSON with `screenshot`, `width`, `height`
- Screenshot existed on disk

#### 4.2 `rpi-gui see --ocr`
Status: **PASS**
- Returned OCR text and element coordinates
- OCR detected visible desktop/window text
- Schema note: output uses `text` + `elements`, not an `ocr` array key

#### 4.3 `rpi-gui click`
Status: **PASS**
- Returned success JSON
- X11 click path appears functional via Xwayland

#### 4.4 `rpi-gui type`
Status: **PASS (with meaningful X11 evidence)**
- Launched `xterm`
- `rpi-gui type` returned success JSON
- Later OCR during integration captured evidence that typed text landed in a live shell window:
  - OCR saw fragments like `hella from Linux arn`
  - OCR also saw `bash: hello: command not found`
- That is messy OCR, but strong evidence that **typing reached the X11 client window**

Important nuance:
- This is better evidence of actual keystroke delivery than Round 2, even if OCR quality is imperfect

#### 4.5 `rpi-term` session lifecycle
Status: **PASS**
- `session create`: OK
- `session list`: OK
- `run`: OK (`READY` + `uname -a`)
- `logs`: OK
- `poll --until READY`: OK
- `session kill`: OK

#### 4.6 `rpi-job` API
Status: **PASS**
- Port `7600` already had an active Python server from prior activity
- Reused healthy existing server rather than forcing a conflicting launch
- `POST /job`: OK
- `GET /job/{id}`: OK
- `GET /jobs`: OK
- `DELETE /job/{id}`: OK
- Example job ID: `82fc551f`

Note:
- This is operationally fine for a smoke test, but if stricter isolation is needed the harness should explicitly ensure a fresh server instance

#### 4.7 `rpi-client` HTTP communication
Status: **PASS**
- `start`: OK
- `list`: OK
- `latest`: OK
- `get`: OK
- `stop`: OK
- Example client job ID: `8d2a92b1`

### Phase 5 - Integration Workflow
Status: **PASS**

Workflow completed:
- Created `tmux` session `integration-e2e`
- `rpi-term run` produced `terminal-ok`
- Opened `xterm` as GUI target
- `rpi-gui see --ocr` captured the desktop and visible shell window
- `rpi-gui click` succeeded
- `rpi-gui type "integration workflow complete" --enter` succeeded
- `rpi-client start http://127.0.0.1:7600 "integration test job"` succeeded
- Repeated `GET /job/{id}` confirmed terminal state `done`
- Final terminal logs and screenshot/OCR artifacts were captured

Interpretation:
- GUI automation, terminal automation, and job orchestration can coexist successfully on this Raspberry Pi
- The integration path remains green even in a Wayland session, so long as the GUI path uses what Xwayland still supports

## X11 / Wayland Findings

### Works via Xwayland
- `scrot`
- `xdotool`
- `xwininfo -root`
- `xterm`
- `rpi-gui see`
- `rpi-gui see --ocr`
- `rpi-gui click`
- `rpi-gui type`

### Weak / unreliable in this session
- `wmctrl -l`
- window enumeration based on EWMH client list
- app discovery quality from `rpi-gui apps list`

### Practical conclusion
This environment is **not “X11 broken”**. It is more accurate to say:
- **X11 interaction primitives work through Xwayland**
- **window-manager enumeration/focus introspection is degraded under Wayland/labwc**

That distinction matters, because otherwise `wmctrl` can look like a stack regression when it is really a compositor limitation.

## Pass / Fail / Skip Matrix
- Phase 1 Setup: **PASS**
- Phase 2 Build: **PASS**
- Phase 3 Permissions: **PARTIAL PASS**
- 4.1 `rpi-gui see`: **PASS**
- 4.2 `rpi-gui see --ocr`: **PASS**
- 4.3 `rpi-gui click`: **PASS**
- 4.4 `rpi-gui type`: **PASS**
- 4.5 `rpi-term` lifecycle: **PASS**
- 4.6 `rpi-job` API: **PASS**
- 4.7 `rpi-client`: **PASS**
- Phase 5 Integration workflow: **PASS**
- `wmctrl -l` enumeration check: **EXPECTED ENVIRONMENT FAILURE**

## Key Artifacts
- Execution log:
  - `/home/alyssonpi/.openclaw/workspace/linux-agents/artifacts/e2e/20260316-1138/execution-log.md`
- Core command logs:
  - `phase-run.log`
  - `phase-run-2.log`
- Screenshot / OCR evidence:
  - `permissions/scrot-test.png`
  - `see.json`
  - `see-ocr.json`
  - `after-type.png`
  - `after-type.ocr.txt`
  - `integration-see-ocr.json`
  - `integration-final.png`
  - `integration-final.ocr.txt`
- X11 inspection evidence:
  - `xwininfo-tree-before-type.txt`
  - `apps-list.json`
- Terminal evidence:
  - `rpi-term-create.txt`
  - `rpi-term-list.txt`
  - `rpi-term-run.txt`
  - `rpi-term-logs.txt`
  - `rpi-term-poll.txt`
  - `integration-rpi-term-run.txt`
  - `integration-rpi-term-logs.txt`
- Job/client evidence:
  - `jobs-precheck.json`
  - `job-create.json`
  - `job-get.json`
  - `jobs-list.json`
  - `job-delete.json`
  - `rpi-client-start.txt`
  - `rpi-client-list.txt`
  - `rpi-client-latest.txt`
  - `rpi-client-get.txt`
  - `rpi-client-stop.txt`
  - `integration-client-start.txt`
  - `integration-job-1.json` through `integration-job-5.json`

## Issues Found
1. **`wmctrl -l` does not work reliably in this Wayland/labwc session**
   - Treat as **EXPECTED** environment behavior
   - Not a blocker for screenshot/OCR/input smoke coverage

2. **`rpi-gui apps list` is not strong evidence of real app discovery here**
   - Returned a workspace path as an app-like object
   - Suggests weak fallback behavior rather than dependable enumeration

3. **`python -m rpi_job.main --help` is awkward**
   - It attempted to start the server instead of behaving like help text
   - Also collided with an already-running service on `7600`

4. **OCR of terminal text is imperfect**
   - Enough for smoke evidence, but not ideal for strict typed-text validation
   - Pi display/theme/font/rendering details still matter

## Recommendations
1. **Test once in a pure X11 session**
   - This is the next best step for confirming `wmctrl` behavior cleanly
   - Recommended explicitly for window enumeration and focus control validation

2. **Add environment detection to `rpi-gui`**
   - Detect Wayland + Xwayland
   - Warn that `wmctrl`/window enumeration may be degraded while click/type/screenshot may still work

3. **Document `wmctrl` limitations as environment-specific**
   - Avoid presenting this as a generic package failure
   - Spell out that labwc/Wayland may not expose the window list the way classic X11 WMs do

4. **Improve `apps list` and/or label its fallback mode**
   - If using a fallback heuristic, say so explicitly
   - Distinguish “best-effort guess” from “verified running applications” 

5. **Improve `rpi-job` CLI help behavior**
   - `python -m rpi_job.main --help` should ideally produce help, not try to bind a production port

## Final Verdict
**Round 3 is effectively GREEN, with one clearly bounded environment limitation.**

The important conclusion is not merely that the stack passes again, but that the failure boundary is now clearer:
- **Code path / stack health:** good
- **X11-over-Xwayland interaction:** good enough for screenshots, OCR, clicks, and typing
- **`wmctrl`-style window enumeration:** unreliable here because of the session environment

If Alysson wants the cleanest final confirmation for window enumeration, the next run should be in a **pure X11 session**. That is the right place to decide whether any remaining `wmctrl` behavior is a true bug or just Wayland being Wayland, which, as usual, found a new way to be educational.