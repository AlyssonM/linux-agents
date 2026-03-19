from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import click

from cron_cli.storage import CrontabManager, TaskRepository


@click.group()
@click.version_option(version="0.1.0", prog_name="cron-cli")
@click.option("--json", "as_json", is_flag=True, help="Emit structured JSON output")
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=Path.home() / ".local" / "share" / "cron-cli",
    show_default=True,
    help="Directory for task metadata and scripts",
)
@click.pass_context
def cli(ctx: click.Context, as_json: bool, data_dir: Path) -> None:
    ctx.ensure_object(dict)
    ctx.obj["json"] = as_json
    ctx.obj["repo"] = TaskRepository(data_dir)
    ctx.obj["crontab"] = CrontabManager()


def _emit(ctx: click.Context, payload: Any, fallback: str | None = None) -> None:
    if ctx.obj["json"]:
        click.echo(json.dumps(payload, indent=2))
        return
    if fallback is not None:
        click.echo(fallback)
        return
    click.echo(str(payload))


def _load_script(script: str | None, script_file: Path | None) -> str:
    if script and script_file:
        raise click.ClickException("use either --script or --script-file, not both")
    if script_file is not None:
        if not script_file.exists():
            raise click.ClickException(f"script file not found: {script_file}")
        return script_file.read_text(encoding="utf-8")
    if script:
        return script
    raise click.ClickException("you must provide --script or --script-file")


def _sync(ctx: click.Context) -> None:
    repo = ctx.obj["repo"]
    crontab = ctx.obj["crontab"]
    crontab.sync_tasks(repo.list_tasks())


@cli.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    repo = ctx.obj["repo"]
    tasks = [task.__dict__ for task in repo.list_tasks()]
    _emit(ctx, {"tasks": tasks}, fallback="\n".join(f"{task['id']} {task['schedule']} {task['name']}" for task in tasks))


@cli.command("get")
@click.argument("task_id")
@click.pass_context
def get_cmd(ctx: click.Context, task_id: str) -> None:
    repo = ctx.obj["repo"]
    try:
        task = repo.get_task(task_id)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(ctx, task.__dict__, fallback=f"{task.id} {task.schedule} {task.name}")


@cli.command("create")
@click.option("--name", required=True, help="Task name")
@click.option("--schedule", required=True, help="Cron schedule (5 fields or @daily-like macro)")
@click.option("--instruction", required=True, help="Task intent/instructions")
@click.option("--script", help="Inline shell script content")
@click.option("--script-file", type=click.Path(path_type=Path), help="Path to shell script file")
@click.option("--enabled/--disabled", default=True, show_default=True)
@click.option("--apply/--no-apply", default=True, show_default=True, help="Sync managed crontab block")
@click.pass_context
def create_cmd(
    ctx: click.Context,
    name: str,
    schedule: str,
    instruction: str,
    script: str | None,
    script_file: Path | None,
    enabled: bool,
    apply: bool,
) -> None:
    repo = ctx.obj["repo"]
    try:
        task = repo.create_task(
            name=name,
            schedule=schedule,
            instruction=instruction,
            script_content=_load_script(script, script_file),
            enabled=enabled,
        )
        if apply:
            _sync(ctx)
    except (ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(ctx, {"created": task.__dict__}, fallback=f"created {task.id}")


@cli.command("update")
@click.argument("task_id")
@click.option("--name", help="New task name")
@click.option("--schedule", help="New cron schedule")
@click.option("--instruction", help="New task instruction")
@click.option("--script", help="Replace script with inline content")
@click.option("--script-file", type=click.Path(path_type=Path), help="Replace script with file content")
@click.option("--enabled/--disabled", default=None)
@click.option("--apply/--no-apply", default=True, show_default=True, help="Sync managed crontab block")
@click.pass_context
def update_cmd(
    ctx: click.Context,
    task_id: str,
    name: str | None,
    schedule: str | None,
    instruction: str | None,
    script: str | None,
    script_file: Path | None,
    enabled: bool | None,
    apply: bool,
) -> None:
    repo = ctx.obj["repo"]
    script_content: str | None = None
    if script is not None or script_file is not None:
        script_content = _load_script(script, script_file)
    try:
        task = repo.update_task(
            task_id=task_id,
            name=name,
            schedule=schedule,
            instruction=instruction,
            script_content=script_content,
            enabled=enabled,
        )
        if apply:
            _sync(ctx)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(ctx, {"updated": task.__dict__}, fallback=f"updated {task.id}")


@cli.command("delete")
@click.argument("task_id")
@click.option("--apply/--no-apply", default=True, show_default=True, help="Sync managed crontab block")
@click.pass_context
def delete_cmd(ctx: click.Context, task_id: str, apply: bool) -> None:
    repo = ctx.obj["repo"]
    try:
        task = repo.delete_task(task_id)
        if apply:
            _sync(ctx)
    except (FileNotFoundError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(ctx, {"deleted": task.__dict__}, fallback=f"deleted {task.id}")


@cli.command("apply")
@click.pass_context
def apply_cmd(ctx: click.Context) -> None:
    try:
        _sync(ctx)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    _emit(ctx, {"status": "ok"}, fallback="crontab synchronized")


@cli.command("run")
@click.argument("task_id")
@click.pass_context
def run_cmd(ctx: click.Context, task_id: str) -> None:
    repo = ctx.obj["repo"]
    try:
        task = repo.get_task(task_id)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    result = subprocess.run(["/bin/bash", task.script_path], capture_output=True, text=True, check=False)
    payload = {
        "task_id": task.id,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode != 0:
        _emit(ctx, payload)
        raise SystemExit(1)
    _emit(ctx, payload, fallback=f"task {task.id} exit={result.returncode}")


if __name__ == "__main__":
    cli()
