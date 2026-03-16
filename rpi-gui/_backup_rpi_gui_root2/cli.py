import click

from rpi_gui.commands.apps import apps_cmd
from rpi_gui.commands.click import click_cmd
from rpi_gui.commands.drag import drag
from rpi_gui.commands.find import find_cmd
from rpi_gui.commands.focus import focus
from rpi_gui.commands.hotkey import hotkey
from rpi_gui.commands.ocr import ocr_cmd
from rpi_gui.commands.screens import screens_cmd
from rpi_gui.commands.see import see_cmd
from rpi_gui.commands.scroll import scroll
from rpi_gui.commands.type import type_cmd
from rpi_gui.commands.window import window_cmd


@click.group(help="GUI automation commands for Raspberry Pi Linux")
def cli() -> None:
    pass


cli.add_command(see_cmd)
cli.add_command(ocr_cmd)
cli.add_command(click_cmd)
cli.add_command(type_cmd)
cli.add_command(hotkey)
cli.add_command(scroll)
cli.add_command(drag)
cli.add_command(focus)
cli.add_command(apps_cmd)
cli.add_command(screens_cmd)
cli.add_command(window_cmd)
cli.add_command(find_cmd, name="find")


if __name__ == "__main__":
    cli()
