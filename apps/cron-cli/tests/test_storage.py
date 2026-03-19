from pathlib import Path

import pytest

from cron_cli.storage import TaskRepository, render_managed_block, validate_schedule


def test_repository_crud(tmp_path: Path):
    repo = TaskRepository(tmp_path)
    task = repo.create_task(
        name="backup",
        schedule="0 2 * * *",
        instruction="Run nightly backup",
        script_content="echo backup",
    )
    fetched = repo.get_task(task.id)
    assert fetched.name == "backup"

    updated = repo.update_task(task.id, schedule="0 3 * * *", enabled=False)
    assert updated.schedule == "0 3 * * *"
    assert updated.enabled is False

    listed = repo.list_tasks()
    assert len(listed) == 1
    assert listed[0].id == task.id

    deleted = repo.delete_task(task.id)
    assert deleted.id == task.id
    assert repo.list_tasks() == []


@pytest.mark.parametrize(
    "schedule",
    ["* * * * *", "0 1 * * 1", "@hourly", "@daily"],
)
def test_validate_schedule_valid(schedule: str):
    validate_schedule(schedule)


@pytest.mark.parametrize(
    "schedule",
    ["", "0 1 * *", "@every_minute", "0 1 * * *\n* * * * *"],
)
def test_validate_schedule_invalid(schedule: str):
    with pytest.raises(ValueError):
        validate_schedule(schedule)


def test_render_only_enabled_tasks(tmp_path: Path):
    repo = TaskRepository(tmp_path)
    enabled = repo.create_task(
        name="enabled",
        schedule="*/5 * * * *",
        instruction="run active",
        script_content="echo active",
        enabled=True,
    )
    repo.create_task(
        name="disabled",
        schedule="*/10 * * * *",
        instruction="run inactive",
        script_content="echo inactive",
        enabled=False,
    )
    lines = render_managed_block(repo.list_tasks())
    text = "\n".join(lines)
    assert enabled.id in text
    assert "disabled" not in text
