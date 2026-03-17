"""
LocalSend airdrop command for rpi-gui.

Alias for 'send' with automatic screenshot - AirDrop-like functionality.
"""

from __future__ import annotations

import click

from rpi_gui.commands.send import send_cmd


@click.command("airdrop")
@click.option("--file", "-f", multiple=True, type=click.Path(exists=True), help="File(s) to send")
@click.option("--target", "-t", help="Target device name (partial match)")
@click.option("--output", type=click.Path(), help="Save screenshot to file before sending")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.pass_context
def airdrop_cmd(ctx, file: tuple, target: str, output: str | None, output_json: bool) -> None:
    """
    AirDrop-like screenshot and send via LocalSend.

    Captures current screen and sends it to a LocalSend device on the network.

    Examples:

        # Quick screenshot + send (auto-discovers device)
        rpi-gui airdrop

        # Screenshot + send to specific device
        rpi-gui airdrop --target "iPhone"

        # Send existing file
        rpi-gui airdrop --file /tmp/document.pdf

        # Screenshot + save + send
        rpi-gui airdrop --output /tmp/screen.png
    """
    # Forward to send_cmd with screenshot=True
    ctx.forward(send_cmd, file=file, screenshot=True, target=target, output=output, output_json=output_json)
