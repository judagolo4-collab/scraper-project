"""
DAG: legislative_projects_etl
Description: ETL para extraer, almacenar y procesar proyectos de ley de múltiples países
Schedule: Diario a las 2 AM
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import sys
import os
import time
import logging

# Agregar path para importar conexiones
sys.path.insert(0, '/opt/airflow/conexiones')

from scraper_service.http_client import ScraperServiceClient
from AWS.s3_client import S3Client
from SQL.postgres_client import PostgresClient

logger = logging.getLogger(__name__)

# Configuración de fuentes de datos
DATA_SOURCES = [
    {
        'country': 'colombia',
        'institution': 'camara',
        'max_pages': None,  # None = todas las páginas
        'classify': True
    },
    # Agregar más países aquí en el futuro
    # {
    #     'country': 'peru',
    #     'institution': 'congreso',
    #     'max_pages': None,
    #     'classify': True
    # },
]

# Argumentos por defecto
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def check_services(**context):
    """Task 0: Verificar que todos los servicios estén disponibles"""
    logger.info("🔍 Checking services health...")
    
    # Verificar Scraper Service
    scraper_client = ScraperServiceClient()
    if not scraper_client.health_check():
        raise Exception("Scraper Service is not available")
    logger.info("✅ Scraper Service: OK")
    
    # Verificar PostgreSQL
    pg_client = PostgresClient()
    try:
        pg_client.connect()
        pg_client.create_tables()
        pg_client.close()
        logger.info("✅ PostgreSQL: OK")
    except Exception as e:
        raise Exception(f"PostgreSQL is not available: {e}")
    
    logger.info("✅ All services are healthy")


def extract_data(source: dict, **context):
    """
    Task 1: Extraer datos del scraper service
    
    :param source: Dict con country, institution, etc.
    """
    execution_date = context['ds']  # YYYY-MM-DD
    country = source['country']
    institution = source['institution']
    
    logger.info(f"🚀 Starting extraction: {country}/{institution}")
    logger.info(f"📅 Execution date: {execution_date}")
    
    start_time = time.time()
    
    # Obtener última fecha de extracción (para carga incremental)
    pg_client = PostgresClient()
    pg_client.connect()
    last_extraction = pg_client.get_last_extraction_date(country, institution)
    pg_client.close()
    
    logger.info(f"📊 Last extraction: {last_extraction or 'None (first time)'}")
    
    # Configurar parámetros para carga incremental
    params = {
        'country': country,
        'institution': institution,
        'max_pages': source.get('max_pages'),
        'classify': source.get('classify', True),
    }
    
    # Si hay extracción previa, hacer carga incremental
    if last_extraction:
        # Convertir YYYY-MM-DD a DD-MM-YYYY
        fecha_parts = last_extraction.split('-')
        fecha_inicio = f"{fecha_parts[2]}-{fecha_parts[1]}-{fecha_parts[0]}"
        params['fecha_inicio'] = fecha_inicio
        logger.info(f"🔄 Incremental load from: {fecha_inicio}")
    
    # Extraer datos
    scraper_client = ScraperServiceClient()
    result = scraper_client.scrape_country(**params)
    
    execution_time = time.time() - start_time
    
    # Guardar en XCom para siguiente task
    context['task_instance'].xcom_push(
        key=f'extraction_result_{country}_{institution}',
        value={
            'country': country,
            'institution': institution,
            'execution_date': execution_date,
            'data': result.get('proyectos', []),
            'total_records': result.get('total_proyectos', 0),
            'execution_time': execution_time,
            'incremental': last_extraction is not None
        }
    )
    
    logger.info(f"✅ Extraction completed in {execution_time:.2f}s")
    logger.info(f"📊 Total records: {result.get('total_proyectos', 0)}")


def save_to_s3_raw(source: dict, **context):
    """
    Task 2: Guardar datos raw en S3
    
    :param source: Dict con country, institution
    """
    country = source['country']
    institution = source['institution']
    
    # Obtener datos de XCom
    extraction_result = context['task_instance'].xcom_pull(
        key=f'extraction_result_{country}_{institution}',
        task_ids=f'extract_{country}_{institution}'
    )
    
    if not extraction_result or not extraction_result['data']:
        logger.warning(f"⚠️ No data to save for {country}/{institution}")
        return
    
    logger.info(f"💾 Saving raw data to S3: {country}/{institution}")
    logger.info(f"📊 Records to save: {extraction_result['total_records']}")
    
    # Guardar en S3
    s3_client = S3Client()
    s3_path = s3_client.save_raw_data(
        data=extraction_result['data'],
        country=country,
        institution=institution,
        execution_date=extraction_result['execution_date']
    )
    
    # Actualizar XCom con path de S3
    extraction_result['s3_raw_path'] = s3_path
    context['task_instance'].xcom_push(
        key=f'extraction_result_{country}_{institution}',
        value=extraction_result
    )
    
    logger.info(f"✅ Raw data saved: {s3_path}")


def process_and_save_to_s3(source: dict, **context):
    """
    Task 3: Procesar datos y guardar versión procesada en S3
    
    :param source: Dict con country, institution
    """
    country = source['country']
    institution = source['institution']
    
    # Obtener datos de XCom
    extraction_result = context['task_instance'].xcom_pull(
        key=f'extraction_result_{country}_{institution}',
        task_ids=f'save_to_s3_raw_{country}_{institution}'
    )
    
    if not extraction_result or not extraction_result['data']:
        logger.warning(f"⚠️ No data to process for {country}/{institution}")
        return
    
    logger.info(f"🔄 Processing data: {country}/{institution}")
    
    # Aquí puedes agregar lógica de procesamiento adicional
    # Por ahora, los datos ya vienen procesados del scraper (con clasificación IA)
    processed_data = extraction_result['data']
    
    # Guardar versión procesada en S3
    s3_client = S3Client()
    s3_processed_path = s3_client.save_processed_data(
        data=processed_data,
        country=country,
        institution=institution,
        execution_date=extraction_result['execution_date']
    )
    
    # Actualizar XCom
    extraction_result['s3_processed_path'] = s3_processed_path
    extraction_result['processed_data'] = processed_data
    context['task_instance'].xcom_push(
        key=f'extraction_result_{country}_{institution}',
        value=extraction_result
    )
    
    logger.info(f"✅ Processed data saved: {s3_processed_path}")


def save_to_postgres(source: dict, **context):
    """
    Task 4: Guardar datos en PostgreSQL
    
    :param source: Dict con country, institution
    """
    country = source['country']
    institution = source['institution']
    
    # Obtener datos de XCom
    extraction_result = context['task_instance'].xcom_pull(
        key=f'extraction_result_{country}_{institution}',
        task_ids=f'process_data_{country}_{institution}'
    )
    
    if not extraction_result or not extraction_result.get('processed_data'):
        logger.warning(f"⚠️ No data to save in DB for {country}/{institution}")
        return
    
    logger.info(f"💾 Saving to PostgreSQL: {country}/{institution}")
    logger.info(f"📊 Records to save: {extraction_result['total_records']}")
    
    # Conectar a PostgreSQL
    pg_client = PostgresClient()
    pg_client.connect()
    
    try:
        # Insertar proyectos
        insert_result = pg_client.insert_proyectos(
            proyectos=extraction_result['processed_data'],
            pais=country,
            institucion=institution,
            s3_raw_path=extraction_result['s3_raw_path']
        )
        
        # Guardar metadata
        pg_client.save_metadata(
            pais=country,
            institucion=institution,
            execution_date=extraction_result['execution_date'],
            total_records=extraction_result['total_records'],
            new_records=insert_result['new'],
            updated_records=insert_result['updated'],
            s3_raw_path=extraction_result['s3_raw_path'],
            s3_processed_path=extraction_result['s3_processed_path'],
            execution_time=extraction_result['execution_time'],
            status='success'
        )
        
        logger.info(f"✅ Data saved to PostgreSQL")
        logger.info(f"   📊 New records: {insert_result['new']}")
        logger.info(f"   🔄 Updated records: {insert_result['updated']}")
        
    except Exception as e:
        logger.error(f"❌ Error saving to PostgreSQL: {e}")
        
        # Guardar metadata de error
        pg_client.save_metadata(
            pais=country,
            institucion=institution,
            execution_date=extraction_result['execution_date'],
            total_records=extraction_result['total_records'],
            new_records=0,
            updated_records=0,
            s3_raw_path=extraction_result.get('s3_raw_path', ''),
            s3_processed_path=extraction_result.get('s3_processed_path', ''),
            execution_time=extraction_result['execution_time'],
            status='error',
            error_message=str(e)
        )
        
        raise
    
    finally:
        pg_client.close()


# Crear DAG
with DAG(
    'legislative_projects_etl',
    default_args=default_args,
    description='ETL para extraer y almacenar proyectos de ley de múltiples países',
    schedule_interval='0 2 * * *',  # Diario a las 2 AM
    catchup=False,
    max_active_runs=1,
    tags=['etl', 'scraping', 'legislative', 'incremental'],
) as dag:
    
    # Task 0: Health check
    check_services_task = PythonOperator(
        task_id='check_services',
        python_callable=check_services,
    )
    
    # Inicio
    start = DummyOperator(task_id='start')
    
    # Fin
    end = DummyOperator(task_id='end')
    
    # Crear tasks para cada fuente de datos
    for source in DATA_SOURCES:
        country = source['country']
        institution = source['institution']
        
        with TaskGroup(group_id=f'{country}_{institution}_etl') as source_group:
            
            # Task 1: Extraer datos
            extract_task = PythonOperator(
                task_id=f'extract_{country}_{institution}',
                python_callable=extract_data,
                op_kwargs={'source': source},
            )
            
            # Task 2: Guardar raw en S3
            save_s3_raw_task = PythonOperator(
                task_id=f'save_to_s3_raw_{country}_{institution}',
                python_callable=save_to_s3_raw,
                op_kwargs={'source': source},
            )
            
            # Task 3: Procesar y guardar en S3
            process_task = PythonOperator(
                task_id=f'process_data_{country}_{institution}',
                python_callable=process_and_save_to_s3,
                op_kwargs={'source': source},
            )
            
            # Task 4: Guardar en PostgreSQL
            save_postgres_task = PythonOperator(
                task_id=f'save_to_postgres_{country}_{institution}',
                python_callable=save_to_postgres,
                op_kwargs={'source': source},
            )
            
            # Definir flujo dentro del grupo
            extract_task >> save_s3_raw_task >> process_task >> save_postgres_task
        
        # Conectar al flujo principal
        start >> check_services_task >> source_group >> end

