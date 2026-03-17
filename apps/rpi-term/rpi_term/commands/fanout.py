import concurrent.futures
import click
from rpi_term.modules import sentinel
from rpi_term.modules.errors import RpiTermError
from rpi_term.modules.output import emit


def _exec_one(session: str, cmd: str, timeout: float) -> dict:
    try:
        code, output = sentinel.run_and_wait(session, cmd, timeout=timeout)
        return {"session": session, "ok": code == 0, "exit_code": code, "output": output}
    except RpiTermError as e:
        return {"session": session, "ok": False, "error": e.code, "message": e.message}


@click.command()
@click.option("--sessions", "targets", required=True, help="Comma-separated session names")
@click.argument("cmd")
@click.option("--timeout", default=30.0)
@click.option("--json", "as_json", is_flag=True)
def fanout(targets: str, cmd: str, timeout: float, as_json: bool):
    sessions = [s.strip() for s in targets.split(",") if s.strip()]
    if not sessions:
        click.echo("Error: No targets specified.", err=True)
        raise SystemExit(1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sessions)) as pool:
        futures = [pool.submit(_exec_one, s, cmd, timeout) for s in sessions]
    results = [f.result() for f in futures]
    order = {s: i for i, s in enumerate(sessions)}
    results.sort(key=lambda x: order.get(x["session"], 999))
    ok = all(r.get("ok", False) for r in results)
    if as_json:
        emit({"ok": ok, "command": cmd, "results": results}, as_json=True, human_lines="")
    else:
        for r in results:
            click.echo(f"--- {r['session']} [{'ok' if r.get('ok') else 'FAIL'}] ---")
            click.echo(r.get("output") or r.get("message") or "")
    if not ok:
        raise SystemExit(1)
