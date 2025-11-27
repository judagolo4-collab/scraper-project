"""
Utilidades generales para DAGs
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def generate_summary(countries: List[str], **context) -> Dict[str, Any]:
    """
    Genera resumen de ejecución para múltiples países.
    
    Args:
        countries: Lista de países procesados
        **context: Contexto de Airflow
        
    Returns:
        Diccionario con el resumen de ejecución
    """
    ti = context['ti']
    
    summary = {
        'execution_date': context['execution_date'].isoformat(),
        'countries': {}
    }
    
    for country in countries:
        total = ti.xcom_pull(key=f'total_{country}', task_ids=f'extract_{country}') or 0
        s3_saved = ti.xcom_pull(key=f's3_saved_{country}', task_ids=f'save_s3_{country}') or 0
        pg_saved = ti.xcom_pull(key=f'pg_saved_{country}', task_ids=f'save_pg_{country}') or 0
        
        summary['countries'][country] = {
            'extracted': total,
            's3_saved': s3_saved,
            'postgres_saved': pg_saved
        }
    
    _log_summary(summary)
    
    return summary


def _log_summary(summary: Dict[str, Any]):
    """Imprime el resumen en los logs."""
    logger.info("=" * 50)
    logger.info("📊 RESUMEN DE EJECUCIÓN")
    logger.info("=" * 50)
    logger.info(f"📅 Fecha: {summary['execution_date']}")
    
    for country, stats in summary['countries'].items():
        logger.info(f"\n{country.upper()}:")
        logger.info(f"  📥 Extraídos: {stats['extracted']}")
        logger.info(f"  💾 S3: {stats['s3_saved']}")
        logger.info(f"  🗄️ PostgreSQL: {stats['postgres_saved']}")
    
    logger.info("=" * 50)

