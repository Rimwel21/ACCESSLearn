"""Processes saved learning materials without blocking FastAPI request workers."""

import logging
import sys
from pathlib import Path

from sqlalchemy.orm import joinedload

import models  # noqa: F401 - register SQLAlchemy relationship targets for the worker process
from database.connection import SessionLocal
from models.teacher_module import TeacherModule
from services.teacher_module_service import _needs_material_topic_regeneration, _process_material_topics


logger = logging.getLogger(__name__)


def process_material(module_id: int) -> None:
    db = SessionLocal()
    try:
        module = (
            db.query(TeacherModule)
            .options(joinedload(TeacherModule.topics))
            .filter(TeacherModule.id == module_id)
            .first()
        )
        if module and _needs_material_topic_regeneration(module):
            _process_material_topics(db, module, Path(module.file_path))
    except Exception:
        logger.exception("Background material processing failed for module %s", module_id)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    process_material(int(sys.argv[1]))
