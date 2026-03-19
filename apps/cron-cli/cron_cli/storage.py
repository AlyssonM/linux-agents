from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
from typing import Iterable
import uuid


CRON_BEGIN = "# BEGIN cron-cli managed tasks"
CRON_END = "# END cron-cli managed tasks"
MACRO_SCHEDULES = {
    "@reboot",
    "@yearly",
    "@annually",
    "@monthly",
    "@weekly",
    "@daily",
    "@midnight",
    "@hourly",
}


@dataclass
class Task:
    id: str
    name: str
    schedule: str
    instruction: str
    script_path: str
    log_path: str
    enabled: bool
    created_at: str
    updated_at: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_schedule(schedule: str) -> None:
    clean = schedule.strip()
    if not clean:
        raise ValueError("schedule cannot be empty")
    if "\n" in clean or "\r" in clean:
        raise ValueError("schedule must be a single line")
    if clean.startswith("@"):
        if clean not in MACRO_SCHEDULES:
            raise ValueError(f"unsupported macro schedule: {clean}")
        return
    if len(clean.split()) != 5:
        raise ValueError("schedule must have 5 cron fields or a supported macro")


class TaskRepository:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.tasks_dir = self.base_dir / "tasks"
        self.scripts_dir = self.base_dir / "scripts"
        self.logs_dir = self.base_dir / "logs"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def default(cls) -> "TaskRepository":
        return cls(Path.home() / ".local" / "share" / "cron-cli")

    def list_tasks(self) -> list[Task]:
        items: list[Task] = []
        for file in sorted(self.tasks_dir.glob("*.json")):
            items.append(self._read_task_file(file))
        return sorted(items, key=lambda task: task.created_at)

    def get_task(self, task_id: str) -> Task:
        path = self.tasks_dir / f"{task_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"task not found: {task_id}")
        return self._read_task_file(path)

    def create_task(
        self,
        name: str,
        schedule: str,
        instruction: str,
        script_content: str,
        enabled: bool = True,
    ) -> Task:
        validate_schedule(schedule)
        task_id = uuid.uuid4().hex[:12]
        script_path = self.scripts_dir / f"{task_id}.sh"
        log_path = self.logs_dir / f"{task_id}.log"
        script_path.write_text(script_content.rstrip() + "\n", encoding="utf-8")
        script_path.chmod(0o700)
        timestamp = now_iso()
        task = Task(
            id=task_id,
            name=name.strip(),
            schedule=schedule.strip(),
            instruction=instruction.strip(),
            script_path=str(script_path),
            log_path=str(log_path),
            enabled=enabled,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._write_task(task)
        return task

    def update_task(
        self,
        task_id: str,
        name: str | None = None,
        schedule: str | None = None,
        instruction: str | None = None,
        script_content: str | None = None,
        enabled: bool | None = None,
    ) -> Task:
        task = self.get_task(task_id)
        if name is not None:
            task.name = name.strip()
        if schedule is not None:
            validate_schedule(schedule)
            task.schedule = schedule.strip()
        if instruction is not None:
            task.instruction = instruction.strip()
        if enabled is not None:
            task.enabled = enabled
        if script_content is not None:
            script_path = Path(task.script_path)
            script_path.write_text(script_content.rstrip() + "\n", encoding="utf-8")
            script_path.chmod(0o700)
        task.updated_at = now_iso()
        self._write_task(task)
        return task

    def delete_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        task_path = self.tasks_dir / f"{task_id}.json"
        if task_path.exists():
            task_path.unlink()
        script_path = Path(task.script_path)
        if script_path.exists():
            script_path.unlink()
        return task

    def _write_task(self, task: Task) -> None:
        path = self.tasks_dir / f"{task.id}.json"
        path.write_text(json.dumps(asdict(task), indent=2), encoding="utf-8")

    @staticmethod
    def _read_task_file(path: Path) -> Task:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return Task(**payload)


class CrontabManager:
    def list_lines(self) -> list[str]:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout.splitlines()
        stderr = result.stderr.lower()
        if "no crontab for" in stderr:
            return []
        raise RuntimeError(result.stderr.strip() or "failed to read crontab")

    def install_lines(self, lines: Iterable[str]) -> None:
        content = "\n".join(lines).rstrip()
        if content:
            content = content + "\n"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as handle:
            handle.write(content)
            temp_path = handle.name
        result = subprocess.run(["crontab", temp_path], capture_output=True, text=True, check=False)
        Path(temp_path).unlink(missing_ok=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "failed to install crontab")

    def sync_tasks(self, tasks: list[Task]) -> None:
        existing = self.list_lines()
        base = strip_managed_block(existing)
        managed = render_managed_block(tasks)
        merged = base + managed
        self.install_lines(merged)


def strip_managed_block(lines: list[str]) -> list[str]:
    out: list[str] = []
    skip = False
    for line in lines:
        if line.strip() == CRON_BEGIN:
            skip = True
            continue
        if line.strip() == CRON_END:
            skip = False
            continue
        if not skip:
            out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return out


def render_managed_block(tasks: list[Task]) -> list[str]:
    enabled_tasks = [task for task in tasks if task.enabled]
    if not enabled_tasks:
        return []
    lines = ["", CRON_BEGIN]
    for task in enabled_tasks:
        script = shlex.quote(task.script_path)
        log = shlex.quote(task.log_path)
        line = f"{task.schedule} /bin/bash {script} >> {log} 2>&1"
        lines.append(f"# cron-cli task_id={task.id} name={task.name}")
        lines.append(line)
    lines.append(CRON_END)
    return lines
