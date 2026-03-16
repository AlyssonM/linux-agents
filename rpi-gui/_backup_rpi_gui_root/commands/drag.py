from __future__ import annotations

import click

from rpi_gui.modules.input import InputError, run_drag


def _parse_point(value: str) -> tuple[int, int]:
    try:
        x_str, y_str = value.split(",", maxsplit=1)
        return int(x_str), int(y_str)
    except Exception as exc:
        raise click.BadParameter("expected format x,y (e.g. 100,200)") from exc


@click.command(help="Drag from one point to another")
@click.option("--from", "from_point", required=True, callback=lambda _ctx, _p, v: _parse_point(v), help="Start point x,y")
@click.option("--to", "to_point", required=True, callback=lambda _ctx, _p, v: _parse_point(v), help="End point x,y")
@click.option("--duration", type=click.FloatRange(0, 30), default=0.2, show_default=True)
@click.option("--button", type=click.Choice(["left", "middle", "right"], case_sensitive=False), default="left", show_default=True)
def drag(from_point: tuple[int, int], to_point: tuple[int, int], duration: float, button: str) -> None:
    try:
        run_drag(
            from_x=from_point[0],
            from_y=from_point[1],
            to_x=to_point[0],
            to_y=to_point[1],
            duration=duration,
            button=button.lower(),
        )
        click.echo(
            f"drag complete: ({from_point[0]},{from_point[1]}) -> ({to_point[0]},{to_point[1]})"
        )
    except InputError as exc:
        raise click.ClickException(str(exc)) from exc
