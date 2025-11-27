"""
Helpers reutilizables para DAGs de Airflow
"""

from .extractors import extract_from_scraper_api
from .storage import save_to_s3, save_to_postgres
from .utils import generate_summary

__all__ = [
    'extract_from_scraper_api',
    'save_to_s3',
    'save_to_postgres',
    'generate_summary',
]

