from __future__ import annotations

import click

from rpi_gui.modules.accessibility import (
    AccessibilityError,
    list_windows,
    maximize_window,
    minimize_window,
    move_window,
    resize_window,
    to_json,
)


@click.group(help="Window management commands")
def window() -> None:
    pass


@window.command(name="list", help="List currently open windows")
def window_list() -> None:
    try:
        data = {"windows": list_windows()}
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(to_json(data))


@window.command(name="move", help="Move a window")
@click.option("--target", required=True, help="Window id, title substring, or wm_class")
@click.option("--x", type=int, required=True, help="Target X")
@click.option("--y", type=int, required=True, help="Target Y")
@click.option("--width", type=int, required=False, help="Optional width")
@click.option("--height", type=int, required=False, help="Optional height")
def window_move(target: str, x: int, y: int, width: int | None, height: int | None) -> None:
    try:
        result = move_window(target=target, x=x, y=y, width=width, height=height)
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(to_json(result))


@window.command(name="resize", help="Resize a window")
@click.option("--target", required=True, help="Window id, title substring, or wm_class")
@click.option("--width", type=int, required=True, help="Width")
@click.option("--height", type=int, required=True, help="Height")
@click.option("--x", type=int, required=False, help="Optional X")
@click.option("--y", type=int, required=False, help="Optional Y")
def window_resize(target: str, width: int, height: int, x: int | None, y: int | None) -> None:
    try:
        result = resize_window(target=target, width=width, height=height, x=x, y=y)
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(to_json(result))


@window.command(name="minimize", help="Minimize a window")
@click.option("--target", required=True, help="Window id, title substring, or wm_class")
def window_minimize(target: str) -> None:
    try:
        result = minimize_window(target=target)
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(to_json(result))


@window.command(name="maximize", help="Maximize a window")
@click.option("--target", required=True, help="Window id, title substring, or wm_class")
def window_maximize(target: str) -> None:
    try:
        result = maximize_window(target=target)
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(to_json(result))
