import click
from rpi_term.modules import proc


@click.group(name="proc")
def proc_cmd():
    pass


@proc_cmd.command("list")
@click.option("--name", default=None)
@click.option("--json", "as_json", is_flag=True)
def list_cmd(name: str | None, as_json: bool):
    ps = [p.to_dict() for p in proc.list_processes(name=name)]
    if as_json:
        click.echo(__import__("json").dumps({"ok": True, "count": len(ps), "processes": ps}, separators=(",", ":")))
    else:
        for p in ps:
            click.echo(f"{p['pid']} {p['name']} {p['state']} {p['command']}")
