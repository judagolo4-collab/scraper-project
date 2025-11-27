"""
Funciones de almacenamiento en S3 y PostgreSQL
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any

from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)


def save_to_s3(
    country: str,
    bucket_name: str = 'scraper-data',
    aws_conn_id: str = 'aws_default',
    **context
) -> int:
    """
    Guarda los datos RAW en S3 organizados por país, fecha y número.
    
    Args:
        country: País de origen de los datos
        bucket_name: Nombre del bucket S3
        aws_conn_id: ID de conexión de AWS en Airflow
        **context: Contexto de Airflow
        
    Returns:
        Número de proyectos guardados
    """
    ti = context['ti']
    proyectos = ti.xcom_pull(key=f'proyectos_{country}', task_ids=f'extract_{country}')
    
    if not proyectos:
        logger.warning(f"⚠️ No hay proyectos de {country} para guardar en S3")
        return 0
    
    logger.info(f"💾 Guardando {len(proyectos)} proyectos de {country} en S3...")
    
    s3_hook = S3Hook(aws_conn_id=aws_conn_id)
    
    # Crear bucket si no existe
    try:
        if not s3_hook.check_for_bucket(bucket_name):
            s3_hook.create_bucket(bucket_name=bucket_name)
            logger.info(f"✅ Bucket '{bucket_name}' creado")
    except Exception as e:
        logger.warning(f"⚠️ Error verificando/creando bucket: {str(e)}")
    
    fecha = datetime.now()
    fecha_path = fecha.strftime('%Y/%m/%d')
    
    saved_count = 0
    
    for proyecto in proyectos:
        try:
            # Obtener número del proyecto
            numero = _get_project_number(proyecto, country)
            numero_clean = numero.replace('/', '_').replace(' ', '_') if numero else f"sin_numero_{saved_count}"
            
            # Crear clave S3
            key = f"raw/{fecha_path}/{country}/{numero_clean}.json"
            
            # Agregar metadata
            proyecto_with_metadata = {
                **proyecto,
                '_metadata': {
                    'extracted_at': fecha.isoformat(),
                    'country': country,
                    'source': 'scraper-api',
                    'version': '1.0'
                }
            }
            
            # Guardar en S3
            s3_hook.load_string(
                string_data=json.dumps(proyecto_with_metadata, ensure_ascii=False, indent=2),
                key=key,
                bucket_name=bucket_name,
                replace=True
            )
            
            saved_count += 1
            
            if saved_count % 100 == 0:
                logger.info(f"📄 Guardados {saved_count}/{len(proyectos)} proyectos...")
                
        except Exception as e:
            logger.error(f"❌ Error guardando proyecto en S3: {str(e)}")
            continue
    
    logger.info(f"✅ S3: {saved_count} proyectos de {country} guardados")
    
    ti.xcom_push(key=f's3_saved_{country}', value=saved_count)
    
    return saved_count


def save_to_postgres(
    country: str,
    postgres_conn_id: str = 'postgres_default',
    **context
) -> int:
    """
    Guarda los datos en PostgreSQL de forma estructurada con UPSERT.
    
    Args:
        country: País de origen de los datos
        postgres_conn_id: ID de conexión de PostgreSQL en Airflow
        **context: Contexto de Airflow
        
    Returns:
        Número de proyectos guardados
    """
    ti = context['ti']
    proyectos = ti.xcom_pull(key=f'proyectos_{country}', task_ids=f'extract_{country}')
    
    if not proyectos:
        logger.warning(f"⚠️ No hay proyectos de {country} para guardar en PostgreSQL")
        return 0
    
    logger.info(f"💾 Guardando {len(proyectos)} proyectos de {country} en PostgreSQL...")
    
    pg_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    
    # SQL UPSERT
    upsert_sql = """
        INSERT INTO proyectos_ley (
            country, numero, numero_camara, numero_senado,
            titulo, titulo_completo, tipo, autores, estado, origen, comision,
            legislatura, resumen, url_detalle, url_pdf, url_gaceta,
            fecha_presentacion, fecha_ultima_reg, sector_economico, source,
            extracted_at, updated_at
        ) VALUES (
            %(country)s, %(numero)s, %(numero_camara)s, %(numero_senado)s,
            %(titulo)s, %(titulo_completo)s, %(tipo)s, %(autores)s, %(estado)s,
            %(origen)s, %(comision)s, %(legislatura)s, %(resumen)s, %(url_detalle)s,
            %(url_pdf)s, %(url_gaceta)s, %(fecha_presentacion)s, %(fecha_ultima_reg)s,
            %(sector_economico)s, %(source)s, %(extracted_at)s, %(updated_at)s
        )
        ON CONFLICT (country, numero)
        DO UPDATE SET
            titulo = EXCLUDED.titulo,
            titulo_completo = EXCLUDED.titulo_completo,
            tipo = EXCLUDED.tipo,
            autores = EXCLUDED.autores,
            estado = EXCLUDED.estado,
            origen = EXCLUDED.origen,
            comision = EXCLUDED.comision,
            legislatura = EXCLUDED.legislatura,
            resumen = EXCLUDED.resumen,
            url_detalle = EXCLUDED.url_detalle,
            url_pdf = EXCLUDED.url_pdf,
            url_gaceta = EXCLUDED.url_gaceta,
            fecha_presentacion = EXCLUDED.fecha_presentacion,
            fecha_ultima_reg = EXCLUDED.fecha_ultima_reg,
            sector_economico = EXCLUDED.sector_economico,
            source = EXCLUDED.source,
            updated_at = EXCLUDED.updated_at;
    """
    
    inserted_count = 0
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    
    try:
        fecha_extraccion = datetime.now()
        
        for proyecto in proyectos:
            try:
                data = _prepare_postgres_data(proyecto, country, fecha_extraccion)
                
                # Validar datos críticos
                if not data['numero']:
                    # Generar ID si no tiene número (hash del título)
                    import hashlib
                    if data['titulo']:
                        titulo_hash = hashlib.md5(data['titulo'].encode()).hexdigest()[:10]
                        data['numero'] = f"SIN_NUM_{titulo_hash}"
                        logger.warning(f"⚠️ Proyecto sin número, generado ID: {data['numero']}")
                    else:
                        logger.warning(f"⚠️ Proyecto sin número ni título, omitiendo")
                        continue
                
                cursor.execute(upsert_sql, data)
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error insertando proyecto: {str(e)}")
                continue
        
        conn.commit()
        logger.info(f"✅ PostgreSQL: {inserted_count} proyectos de {country} guardados")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error en transacción PostgreSQL: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    ti.xcom_push(key=f'pg_saved_{country}', value=inserted_count)
    
    return inserted_count


def _get_project_number(proyecto: Dict[str, Any], country: str) -> str:
    """Obtiene el número del proyecto según el país."""
    # Intentar todos los campos posibles de número
    return (
        proyecto.get('numero') or 
        proyecto.get('numero_camara') or 
        proyecto.get('numero_senado') or 
        ''
    )


def _prepare_postgres_data(proyecto: Dict[str, Any], country: str, fecha: datetime) -> Dict[str, Any]:
    """Prepara los datos para insertar en PostgreSQL."""
    return {
        'country': country,
        'numero': _get_project_number(proyecto, country),
        'numero_camara': proyecto.get('numero_camara'),
        'numero_senado': proyecto.get('numero_senado'),
        'titulo': proyecto.get('titulo'),
        'titulo_completo': proyecto.get('titulo_completo'),
        'tipo': proyecto.get('tipo'),
        'autores': proyecto.get('autores'),
        'estado': proyecto.get('estado'),
        'origen': proyecto.get('origen'),
        'comision': proyecto.get('comision'),
        'legislatura': proyecto.get('legislatura'),
        'resumen': proyecto.get('resumen'),
        'url_detalle': proyecto.get('url_detalle'),
        'url_pdf': proyecto.get('url_pdf'),
        'url_gaceta': proyecto.get('url_gaceta'),
        'fecha_presentacion': proyecto.get('fecha_presentacion'),
        'fecha_ultima_reg': proyecto.get('fecha_ultima_reg'),
        'sector_economico': proyecto.get('sector_economico'),
        'source': proyecto.get('source'),
        'extracted_at': fecha,
        'updated_at': fecha
    }

