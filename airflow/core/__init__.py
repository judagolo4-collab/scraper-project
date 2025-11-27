"""
Core tasks reutilizables para DAGs
"""

from .scraper_tasks import (
    create_extract_task,
    create_s3_task,
    create_postgres_task,
    create_summary_task
)

__all__ = [
    'create_extract_task',
    'create_s3_task',
    'create_postgres_task',
    'create_summary_task',
]

