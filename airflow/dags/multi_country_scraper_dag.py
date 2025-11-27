# multi_country_scraper_dag_v2.py - DAG limpio y modular

from airflow import DAG
from datetime import timedelta
import pendulum
import sys
from pathlib import Path

# Agregar paths para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scraper_tasks import (
    create_extract_task,
    create_s3_task,
    create_postgres_task,
    create_summary_task
)

# ============================================================
# CONFIGURACIÓN DEL DAG
# ============================================================

DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

COUNTRIES = ['colombia', 'peru']

# ============================================================
# DEFINICIÓN DEL DAG
# ============================================================

with DAG(
    'multi_country_scraper',
    default_args=DEFAULT_ARGS,
    description='Scraping multi-país (Colombia + Perú) con almacenamiento en S3 y PostgreSQL',
    schedule='0 2 * * *',  # Diario a las 2 AM
    start_date=pendulum.today('UTC').add(days=-1),
    catchup=False,
    tags=['scraping', 'multi-country', 's3', 'postgres'],
) as dag:
    
    # ============================================================
    # CREAR TASKS PARA CADA PAÍS
    # ============================================================
    
    extract_tasks = {}
    s3_tasks = {}
    pg_tasks = {}
    
    for country in COUNTRIES:
        # Task de extracción
        extract_tasks[country] = create_extract_task(
            dag=dag,
            country=country,
            max_pages=10,
            classify=True
        )
        
        # Task de S3
        s3_tasks[country] = create_s3_task(
            dag=dag,
            country=country
        )
        
        # Task de PostgreSQL
        pg_tasks[country] = create_postgres_task(
            dag=dag,
            country=country
        )
    
    # Task de resumen
    summary = create_summary_task(
        dag=dag,
        countries=COUNTRIES
    )
    
    # ============================================================
    # DEFINIR FLUJO
    # ============================================================
    
    # Procesar cada país: extract → [s3 + pg]
    for country in COUNTRIES:
        extract_tasks[country] >> [s3_tasks[country], pg_tasks[country]] >> summary

