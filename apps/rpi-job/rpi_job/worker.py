from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"


def update(job_id: str, **kwargs) -> None:
    p = JOBS_DIR / f"{job_id}.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data.update(kwargs)
    p.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


def main(job_id: str, prompt: str) -> None:
    logger.info("Worker started for job=%s", job_id)
    try:
        for i in range(3):
            time.sleep(0.3)
            p = JOBS_DIR / f"{job_id}.yaml"
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            updates = data.get("updates") or []
            updates.append(f"step {i + 1}/3")
            data["updates"] = updates
            p.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")
        update(job_id, status="done", summary=f"Completed: {prompt[:120]}")
    except Exception as exc:
        logger.exception("Worker failed for job=%s", job_id)
        update(job_id, status="failed", summary=str(exc))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
