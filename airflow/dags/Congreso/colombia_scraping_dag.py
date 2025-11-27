from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Agregar directorio raíz al path para importar conexiones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from conexiones.scraper_service.http_client import ScraperHttpClient
from conexiones.SQL.postgres_client import PostgresClient

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'colombia_scraping_dag',
    default_args=default_args,
    description='Scraping de proyectos de ley de Colombia',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['colombia', 'scraping'],
) as dag:

    def scrape_task(**context):
        client = ScraperHttpClient()
        # Ejemplo: Filtrar desde hace 7 días
        # fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%d-%m-%Y')
        # Por ahora traemos todo o usamos un parámetro
        
        # Leer configuración de ejecución manual si existe
        conf = context['dag_run'].conf or {}
        fecha_inicio = conf.get('fecha_inicio')
        max_pages = conf.get('max_pages')
        
        print(f"🚀 Iniciando scraping. Fecha inicio: {fecha_inicio}, Max pages: {max_pages}")
        result = client.scrape_colombia(fecha_inicio=fecha_inicio, max_pages=max_pages)
        
        # Pasar resultados a la siguiente tarea via XCom
        # Nota: Si son muchos datos, mejor guardar en S3/GCS intermedio. 
        # Para este MVP, XCom está bien si no son miles de proyectos en una sola ejecución.
        return result['proyectos']

    def save_task(**context):
        proyectos = context['task_instance'].xcom_pull(task_ids='ejecutar_scraper')
        if not proyectos:
            print("⚠️ No se recibieron proyectos para guardar")
            return
            
        print(f"💾 Guardando {len(proyectos)} proyectos en DB...")
        pg_client = PostgresClient()
        pg_client.init_db() # Asegurar que la tabla existe
        pg_client.save_projects(proyectos)
        print("✅ Guardado exitoso")

    t1 = PythonOperator(
        task_id='ejecutar_scraper',
        python_callable=scrape_task,
        provide_context=True,
    )

    t2 = PythonOperator(
        task_id='guardar_en_postgres',
        python_callable=save_task,
        provide_context=True,
    )

    t1 >> t2
