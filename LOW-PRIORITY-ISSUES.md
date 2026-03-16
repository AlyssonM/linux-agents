# Low-Priority Issues

## Documented Issues (Non-Blocking)

These issues are documented for future improvement but do not block production use.

---

### 1. rpi-gui: Focus Window Title Matching

**Status:** Documented limitation  
**Severity:** Low  
**Impact:** `rpi-gui focus` may not match window titles consistently

**Issue:**
The `focus_window()` function uses xdotool to search for windows by title. Matching behavior depends on xdotool's implementation and may not work consistently across all window managers.

**Workaround:**
```bash
# Use window ID instead of title
rpi-gui window list  # Get window IDs
rpi-gui focus --exact <window-id>

# Or use coordinate-based clicking
rpi-gui click --x 100 --y 200
```

**Technical Details:**
- xdotool uses substring matching by default
- `--exact` flag enables regex pattern matching
- X11 window matching can be inconsistent
- Works best with unique window titles

**Future Improvements:**
- Add fuzzy matching algorithm
- Cache window ID mappings
- Support multiple matching strategies

---

### 2. rpi-gui: Window Maximize Syntax

**Status:** Documented CLI behavior  
**Severity:** Low  
**Impact:** Command may fail if syntax is incorrect

**Issue:**
The `window maximize` command requires `--target` flag, but users may try positional arguments.

**Current Syntax:**
```bash
# ✅ Correct
rpi-gui window maximize --target <window-id>

# ❌ Incorrect (will fail)
rpi-gui window maximize <window-id>
```

**Workaround:**
Always use the `--target` flag as documented.

**Future Improvements:**
- Add better error messages
- Support positional arguments
- Add help examples

---

### 3. rpi-job: Stop Race Condition

**Status:** Known race condition  
**Severity:** Low  
**Impact:** Job may show completion updates even after being stopped

**Issue:**
When stopping a job:
1. Server sends SIGTERM to worker process
2. Worker process may still be executing
3. Worker may write completion updates before exiting
4. Job status shows "stopped" but has completion data

**Example:**
```yaml
id: "47119b48"
status: "stopped"
summary: "Command completed"  # Worker wrote this before SIGTERM took effect
updates:
  - "Starting job..."
  - "Running..."
  - "Completed!"  # Written after stop request
```

**Workaround:**
This is a cosmetic issue - the job is actually stopped, but may show stale completion data.

**Technical Details:**
- Classic race condition between stop request and worker execution
- SIGTERM is asynchronous - worker has time to finish
- Proper fix requires worker to handle signals synchronously

**Future Improvements:**
- Worker should check for stop flag during execution
- Add signal handler in worker to clean exit
- Separate "stopped" status from completion data

**Current Mitigation:**
- Job is stopped (process killed)
- Only status reporting is affected
- Does not affect actual job execution

---

## Testing Workarounds

### Focus Window
```bash
# List windows to get IDs
rpi-gui window list

# Use ID for reliable focus
rpi-gui focus --exact "0x1200001"

# Or coordinate-based
rpi-gui click --x 500 --y 300
```

### Window Maximize
```bash
# Always use --target flag
rpi-gui window maximize --target "0x1200001"

# Or resize manually
rpi-gui window resize --target "xterm" --width 1920 --height 1080
```

### Job Stop
```bash
# Stop works correctly
rpi-gui-client stop http://127.0.0.1:7600 <job-id>

# Job will be stopped
# May show stale completion data (cosmetic only)
```

---

## Severity Classification

**Low Priority Criteria:**
- Does not block core functionality
- Has documented workarounds
- Affects edge cases only
- Cosmetic/user-experience issues

**Why Non-Blocking:**
- GUI automation works (focus can use coordinates)
- Window management works (maximize syntax is documented)
- Job server works (stop kills process, only status reporting affected)

---

**Documented:** 2026-03-16  
**Status:** Production ready with these documented limitations
