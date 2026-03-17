"""
LocalSend send/airdrop command for rpi-gui.

Send files via LocalSend protocol (AirDrop-like functionality).
"""

from __future__ import annotations

import json

import click

from rpi_gui.modules.localsend import LocalSendError, discover_and_send
from rpi_gui.modules.screenshot import capture_screenshot, save_screenshot


@click.command("send")
@click.option("--file", "-f", multiple=True, type=click.Path(exists=True), help="File(s) to send")
@click.option("--screenshot", is_flag=True, help="Capture and send current screen")
@click.option("--target", "-t", help="Target device name (partial match)")
@click.option("--output", type=click.Path(), help="Save screenshot to file before sending")
def send_cmd(file: tuple, screenshot: bool, target: str, output: str | None) -> None:
    """
    Send files via LocalSend (AirDrop-like transfer).

    Examples:

        # Send file to discovered device
        rpi-gui send --file /tmp/document.pdf

        # Send multiple files
        rpi-gui send --file img1.png --file img2.jpg

        # Capture screenshot and send
        rpi-gui send --screenshot

        # Send screenshot to specific device
        rpi-gui send --screenshot --target "iPhone"

        # Save screenshot and send
        rpi-gui send --screenshot --output /tmp/screen.png --file /tmp/screen.png
    """
    files = list(file)

    # Capturar screenshot se solicitado
    if screenshot:
        try:
            image = capture_screenshot()
            saved_path = save_screenshot(image=image, output_path=output)

            click.echo(f"📸 Screenshot saved: {saved_path}")
            files.append(str(saved_path))
        except Exception as exc:
            raise click.ClickException(f"Screenshot failed: {exc}") from exc

    # Verificar arquivos
    if not files:
        raise click.ClickException("No files specified. Use --file or --screenshot")

    # Enviar via LocalSend
    try:
        click.echo(f"📡 Sending {len(files)} file(s) via LocalSend...\n")

        if target:
            click.echo(f"🎯 Target: {target}")

        result = discover_and_send(files, target_name=target)

        # Resultados
        click.echo(f"\n✅ Sent to: {result['device']} ({result['host']})")
        click.echo(f"📊 Files: {result['files_sent']}/{result['files_total']} sent")

        if result['files_sent'] < result['files_total']:
            click.echo("\n⚠️  Some files failed:")
            for r in result['results']:
                if not r.get('success'):
                    click.echo(f"   ❌ {r.get('file', 'unknown')}: {r.get('error', 'unknown error')}")

        click.echo(f"\n{json.dumps(result, ensure_ascii=False, indent=2)}")

    except LocalSendError as exc:
        raise click.ClickException(str(exc)) from exc


@click.command("airdrop")
@click.option("--file", "-f", multiple=True, type=click.Path(exists=True), help="File(s) to send")
@click.option("--target", "-t", help="Target device name (partial match)")
@click.pass_context
def airdrop_cmd(ctx, file: tuple, target: str) -> None:
    """
    Alias for 'send' with automatic screenshot.

    Captures screen and sends via LocalSend (AirDrop-like).

    Example:

        # Quick screenshot + send
        rpi-gui airdrop

        # Screenshot + send to specific device
        rpi-gui airdrop --target "Pixel 8"
    """
    # Reutilizar send_cmd com screenshot=True
    ctx.forward(send_cmd, file=file, screenshot=True, target=target)
