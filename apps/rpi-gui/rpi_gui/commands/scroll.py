from __future__ import annotations

import click

from rpi_gui.modules.input import run_scroll


@click.command("scroll", help="Scroll screen up/down by steps")
@click.argument("direction", type=click.Choice(["up", "down"], case_sensitive=False))
@click.argument("steps", type=click.IntRange(1, 1000))
@click.option("--clicks-per-step", type=click.IntRange(1, 10000), default=120, show_default=True)
def scroll_cmd(direction: str, steps: int, clicks_per_step: int) -> None:
    try:
        amount = run_scroll(direction, steps, clicks_per_step=clicks_per_step)
        click.echo(f"scrolled {direction.lower()} (amount={abs(amount)})")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
