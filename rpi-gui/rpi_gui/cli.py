from __future__ import annotations

import logging

import click

from rpi_gui.commands.airdrop import airdrop_cmd
from rpi_gui.commands.apps import apps_cmd
from rpi_gui.commands.click import click_cmd
from rpi_gui.commands.drag import drag_cmd
from rpi_gui.commands.find import find_cmd
from rpi_gui.commands.focus import focus_cmd
from rpi_gui.commands.hotkey import hotkey_cmd
from rpi_gui.commands.ocr import ocr_cmd
from rpi_gui.commands.screens import screens_cmd
from rpi_gui.commands.scroll import scroll_cmd
from rpi_gui.commands.see import see_cmd
from rpi_gui.commands.send import send_cmd
from rpi_gui.commands.type import type_cmd
from rpi_gui.commands.window import window_cmd


@click.group(help="rpi-gui: Core GUI automation for Linux ARM64")
@click.option("--verbose", is_flag=True, help="Enable debug logs")
def cli(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


cli.add_command(see_cmd, name="see")
cli.add_command(ocr_cmd, name="ocr")
cli.add_command(click_cmd, name="click")
cli.add_command(type_cmd, name="type")
cli.add_command(apps_cmd, name="apps")
cli.add_command(screens_cmd, name="screens")
cli.add_command(window_cmd, name="window")
cli.add_command(find_cmd, name="find")
cli.add_command(hotkey_cmd, name="hotkey")
cli.add_command(scroll_cmd, name="scroll")
cli.add_command(drag_cmd, name="drag")
cli.add_command(focus_cmd, name="focus")
cli.add_command(send_cmd, name="send")
cli.add_command(airdrop_cmd, name="airdrop")


if __name__ == "__main__":
    cli()
