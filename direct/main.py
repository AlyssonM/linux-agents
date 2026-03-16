from __future__ import annotations

import click

import client


@click.group()
def cli() -> None:
    """CLI client for the linux-agents listen server."""


@cli.command()
@click.argument("url")
@click.argument("prompt")
def start(url: str, prompt: str) -> None:
    """Start a new Codex agent job."""
    result = client.start_job(url, prompt)
    click.echo(result["job_id"])


@cli.command()
@click.argument("url")
@click.argument("job_id")
def get(url: str, job_id: str) -> None:
    """Get the current state of a job."""
    click.echo(client.get_job(url, job_id))


@cli.command("list")
@click.argument("url")
@click.option("--archived", is_flag=True, help="Show archived jobs only.")
def list_cmd(url: str, archived: bool) -> None:
    """List all jobs."""
    click.echo(client.list_jobs(url, archived=archived))


@cli.command()
@click.argument("url")
def clear(url: str) -> None:
    """Archive all jobs."""
    result = client.clear_jobs(url)
    click.echo(f"Archived {result['archived']} job(s)")


@cli.command()
@click.argument("url")
@click.argument("n", default=1, type=int)
def latest(url: str, n: int) -> None:
    """Show full details of the latest N jobs."""
    click.echo(client.latest_jobs(url, n))


@cli.command()
@click.argument("url")
@click.argument("job_id")
def stop(url: str, job_id: str) -> None:
    """Stop a running job."""
    result = client.stop_job(url, job_id)
    click.echo(f"Job {result['job_id']} {result['status']}")


if __name__ == "__main__":
    cli()
