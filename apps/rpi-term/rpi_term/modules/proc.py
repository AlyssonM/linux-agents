import os
import time
from dataclasses import dataclass
import psutil
from rpi_term.modules import tmux


@dataclass
class ProcessInfo:
    pid: int
    ppid: int
    name: str
    command: str
    cpu: float
    memory_mb: float
    elapsed: str
    state: str

    def to_dict(self) -> dict:
        return vars(self)


def _elapsed(create_time: float) -> str:
    s = int(time.time() - create_time)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    return f"{s // 3600}h{(s % 3600) // 60:02d}m"


def list_processes(name: str | None = None) -> list[ProcessInfo]:
    uid = os.getuid()
    out = []
    for p in psutil.process_iter(["pid", "ppid", "name", "cmdline", "cpu_percent", "memory_info", "create_time", "status", "uids"]):
        try:
            if p.info.get("uids") and p.info["uids"].real != uid:
                continue
            cmd = " ".join(p.info.get("cmdline") or []) or (p.info.get("name") or "")
            if name and name.lower() not in cmd.lower() and name.lower() not in (p.info.get("name") or "").lower():
                continue
            mem = p.info.get("memory_info")
            out.append(ProcessInfo(
                pid=p.info["pid"], ppid=p.info.get("ppid") or 0, name=p.info.get("name") or "",
                command=cmd, cpu=float(p.info.get("cpu_percent") or 0.0),
                memory_mb=round((mem.rss / (1024*1024)), 1) if mem else 0.0,
                elapsed=_elapsed(float(p.info.get("create_time") or time.time())),
                state=p.info.get("status") or "unknown",
            ))
        except Exception:
            continue
    return sorted(out, key=lambda x: x.pid)
