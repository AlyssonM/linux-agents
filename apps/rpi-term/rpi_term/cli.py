import logging

import click
from rpi_term.commands.session import session
from rpi_term.commands.run import run
from rpi_term.commands.send import send
from rpi_term.commands.logs import logs
from rpi_term.commands.poll import poll
from rpi_term.commands.fanout import fanout
from rpi_term.commands.proc import proc_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="rpi-term")
@click.option("--verbose", is_flag=True, help="Enable debug logs")
def cli(verbose: bool):
    """tmux-based terminal automation for Linux ARM64 agents."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


cli.add_command(session)
cli.add_command(run)
cli.add_command(send)
cli.add_command(logs)
cli.add_command(poll)
cli.add_command(fanout)
cli.add_command(proc_cmd)


if __name__ == "__main__":
    cli()
