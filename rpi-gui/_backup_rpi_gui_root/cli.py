import click

from rpi_gui.commands.drag import drag
from rpi_gui.commands.focus import focus
from rpi_gui.commands.hotkey import hotkey
from rpi_gui.commands.scroll import scroll


@click.group(help="GUI automation commands for Raspberry Pi Linux")
def cli() -> None:
    pass


cli.add_command(hotkey)
cli.add_command(scroll)
cli.add_command(drag)
cli.add_command(focus)


if __name__ == "__main__":
    cli()
