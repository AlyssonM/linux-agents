from __future__ import annotations

import click

from rpi_gui.modules.accessibility import (
    AccessibilityError,
    maximize_window,
    minimize_window,
    move_window,
    resize_window,
    to_json,
)


@click.group(name="window", help="Window management commands")
def window_cmd() -> None:
    pass


@window_cmd.command(name="move")
@click.option("--target", required=True)
@click.option("--x", type=int, required=True)
@click.option("--y", type=int, required=True)
@click.option("--width", type=int, default=None)
@click.option("--height", type=int, default=None)
def window_move_cmd(target: str, x: int, y: int, width: int | None, height: int | None) -> None:
    try:
        click.echo(to_json(move_window(target=target, x=x, y=y, width=width, height=height)))
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc


@window_cmd.command(name="resize")
@click.option("--target", required=True)
@click.option("--width", type=int, required=True)
@click.option("--height", type=int, required=True)
@click.option("--x", type=int, default=None)
@click.option("--y", type=int, default=None)
def window_resize_cmd(target: str, width: int, height: int, x: int | None, y: int | None) -> None:
    try:
        click.echo(to_json(resize_window(target=target, width=width, height=height, x=x, y=y)))
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc


@window_cmd.command(name="minimize")
@click.option("--target", required=True)
def window_minimize_cmd(target: str) -> None:
    try:
        click.echo(to_json(minimize_window(target=target)))
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc


@window_cmd.command(name="maximize")
@click.option("--target", required=True)
def window_maximize_cmd(target: str) -> None:
    try:
        click.echo(to_json(maximize_window(target=target)))
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
