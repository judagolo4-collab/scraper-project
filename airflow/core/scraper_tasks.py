"""
Tareas core reutilizables para scrapers
"""

from airflow.operators.python import PythonOperator
from helpers import extract_from_scraper_api, save_to_s3, save_to_postgres, generate_summary


def create_extract_task(dag, country: str, task_id: str = None, **kwargs):
    """
    Crea una task de extracción para un país.
    
    Args:
        dag: DAG de Airflow
        country: País a scrapear
        task_id: ID de la task (opcional, por defecto: extract_{country})
        **kwargs: Argumentos adicionales para el scraper
        
    Returns:
        PythonOperator configurado
    """
    task_id = task_id or f'extract_{country}'
    
    return PythonOperator(
        task_id=task_id,
        python_callable=extract_from_scraper_api,
        op_kwargs={'country': country, **kwargs},
        dag=dag,
    )


def create_s3_task(dag, country: str, task_id: str = None, bucket_name: str = 'scraper-data'):
    """
    Crea una task de almacenamiento en S3 para un país.
    
    Args:
        dag: DAG de Airflow
        country: País de origen
        task_id: ID de la task (opcional, por defecto: save_s3_{country})
        bucket_name: Nombre del bucket S3
        
    Returns:
        PythonOperator configurado
    """
    task_id = task_id or f'save_s3_{country}'
    
    return PythonOperator(
        task_id=task_id,
        python_callable=save_to_s3,
        op_kwargs={'country': country, 'bucket_name': bucket_name},
        dag=dag,
    )


def create_postgres_task(dag, country: str, task_id: str = None, conn_id: str = 'postgres_default'):
    """
    Crea una task de almacenamiento en PostgreSQL para un país.
    
    Args:
        dag: DAG de Airflow
        country: País de origen
        task_id: ID de la task (opcional, por defecto: save_pg_{country})
        conn_id: ID de conexión de PostgreSQL
        
    Returns:
        PythonOperator configurado
    """
    task_id = task_id or f'save_pg_{country}'
    
    return PythonOperator(
        task_id=task_id,
        python_callable=save_to_postgres,
        op_kwargs={'country': country, 'postgres_conn_id': conn_id},
        dag=dag,
    )


def create_summary_task(dag, countries: list, task_id: str = 'generate_summary'):
    """
    Crea una task de resumen para múltiples países.
    
    Args:
        dag: DAG de Airflow
        countries: Lista de países procesados
        task_id: ID de la task (por defecto: generate_summary)
        
    Returns:
        PythonOperator configurado
    """
    return PythonOperator(
        task_id=task_id,
        python_callable=generate_summary,
        op_kwargs={'countries': countries},
        dag=dag,
    )

