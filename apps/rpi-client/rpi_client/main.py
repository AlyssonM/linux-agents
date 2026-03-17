from __future__ import annotations

import logging

import click

from rpi_client import client


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@click.group()
@click.option("--verbose", is_flag=True, help="Enable debug logs")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """CLI client for rpi-job server."""
    setup_logging(verbose)
    ctx.ensure_object(dict)


@cli.command("start")
@click.argument("url")
@click.argument("prompt")
@click.option("--agent", help="Agent to use (codex, claude, openclaw, opencode, pi)")
@click.option("--model", help="Model to use")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def start_cmd(url: str, prompt: str, agent: str | None, model: str | None, output_json: bool) -> None:
    try:
        res = client.start_job(url, prompt, agent=agent, model=model)
        if output_json:
            import json
            click.echo(json.dumps(res))
        else:
            click.echo(res["job_id"])
    except client.ClientError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("get")
@click.argument("url")
@click.argument("job_id")
def get_cmd(url: str, job_id: str) -> None:
    try:
        click.echo(client.get_job(url, job_id))
    except client.ClientError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("list")
@click.argument("url")
@click.option("--archived", is_flag=True)
def list_cmd(url: str, archived: bool) -> None:
    try:
        click.echo(client.list_jobs(url, archived=archived))
    except client.ClientError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("stop")
@click.argument("url")
@click.argument("job_id")
def stop_cmd(url: str, job_id: str) -> None:
    try:
        out = client.stop_job(url, job_id)
        click.echo(f"Job {out['job_id']} {out['status']}")
    except client.ClientError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("latest")
@click.argument("url")
@click.option("-n", default=1, type=click.IntRange(1, 100))
def latest_cmd(url: str, n: int) -> None:
    try:
        click.echo(client.latest_jobs(url, n))
    except client.ClientError as exc:
        raise click.ClickException(str(exc)) from exc


if __name__ == "__main__":
    cli()
