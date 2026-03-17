from __future__ import annotations

import click

from rpi_gui.modules.input import run_hotkey


@click.command("hotkey", help="Press keyboard shortcut, e.g. ctrl+s or ctrl+shift+esc")
@click.argument("shortcut", nargs=-1, required=True)
def hotkey_cmd(shortcut: tuple[str, ...]) -> None:
    try:
        keys: list[str] = []
        for token in shortcut:
            keys.extend(part for part in token.split("+") if part.strip())
        run_hotkey(keys)
        click.echo(f"hotkey sent: {'+'.join(keys)}")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
