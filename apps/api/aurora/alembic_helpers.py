from __future__ import annotations

"""Tiny helper to programmatically create an initial Alembic revision.
Run via `python -m apps.api.aurora.alembic_helpers` if you prefer code-first.
"""

from alembic import command
from alembic.config import Config
from pathlib import Path


def get_cfg() -> Config:
    root = Path(__file__).resolve().parents[3]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    return cfg


def create_initial_revision(message: str = "init") -> None:
    cfg = get_cfg()
    command.revision(cfg, autogenerate=True, message=message)


def upgrade_head() -> None:
    cfg = get_cfg()
    command.upgrade(cfg, "head")


if __name__ == "__main__":
    create_initial_revision()
    upgrade_head()
