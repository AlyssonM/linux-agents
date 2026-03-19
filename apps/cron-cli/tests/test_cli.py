from pathlib import Path

from click.testing import CliRunner

from cron_cli.main import cli
from cron_cli.storage import CrontabManager


def test_create_and_list_json(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(CrontabManager, "sync_tasks", lambda self, tasks: None)
    runner = CliRunner()
    create = runner.invoke(
        cli,
        [
            "--json",
            "--data-dir",
            str(tmp_path),
            "create",
            "--name",
            "healthcheck",
            "--instruction",
            "validate endpoint",
            "--schedule",
            "*/5 * * * *",
            "--script",
            "echo ok",
        ],
    )
    assert create.exit_code == 0
    assert '"created"' in create.output

    listing = runner.invoke(cli, ["--json", "--data-dir", str(tmp_path), "list"])
    assert listing.exit_code == 0
    assert '"tasks"' in listing.output
    assert "healthcheck" in listing.output


def test_update_and_delete(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(CrontabManager, "sync_tasks", lambda self, tasks: None)
    runner = CliRunner()
    create = runner.invoke(
        cli,
        [
            "--json",
            "--data-dir",
            str(tmp_path),
            "create",
            "--name",
            "rotate-log",
            "--instruction",
            "rotate log",
            "--schedule",
            "0 * * * *",
            "--script",
            "echo rotate",
        ],
    )
    assert create.exit_code == 0
    task_id = create.output.split('"id": "')[1].split('"')[0]

    update = runner.invoke(
        cli,
        [
            "--json",
            "--data-dir",
            str(tmp_path),
            "update",
            task_id,
            "--schedule",
            "30 * * * *",
            "--instruction",
            "rotate log every half hour",
        ],
    )
    assert update.exit_code == 0
    assert "30 * * * *" in update.output

    delete = runner.invoke(cli, ["--json", "--data-dir", str(tmp_path), "delete", task_id])
    assert delete.exit_code == 0
    assert '"deleted"' in delete.output
