"""
Funciones de extracción de datos desde APIs
"""

import logging
import requests

logger = logging.getLogger(__name__)


def extract_from_scraper_api(
    country: str,
    scraper_url: str = "http://scraper-api:8000/api/scrape",
    tipo_scraper: str = None,
    max_pages: int = 10,
    classify: bool = True,
    timeout: int = 600,
    **context
) -> int:
    """
    Extrae datos del servicio de scraping para un país específico.
    
    Args:
        country: País a scrapear (colombia, peru, etc.)
        scraper_url: URL base del servicio de scraping
        tipo_scraper: Tipo de scraper (ajax, selenium, etc.)
        max_pages: Número máximo de páginas a scrapear
        classify: Si debe clasificar con Gemini AI
        timeout: Timeout en segundos
        **context: Contexto de Airflow
        
    Returns:
        Número total de proyectos extraídos
    """
    ti = context['ti']
    
    logger.info(f"🚀 Iniciando extracción de {country}...")
    
    # Determinar tipo de scraper si no se especificó
    if not tipo_scraper:
        tipo_scraper = 'ajax' if country == 'colombia' else 'selenium'
    
    # Construir URL
    url = f"{scraper_url}/{country}"
    
    # Parámetros
    params = {
        'tipo_scraper': tipo_scraper,
        'max_pages': max_pages,
        'classify': classify,
    }
    
    try:
        logger.info(f"📡 Llamando a: {url}")
        logger.info(f"📋 Parámetros: {params}")
        
        response = requests.post(url, params=params, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('success'):
            raise Exception(f"Scraping falló: {data.get('message')}")
        
        proyectos = data.get('proyectos', [])
        total = len(proyectos)
        
        logger.info(f"✅ Extracción completada: {total} proyectos de {country}")
        
        # Guardar en XCom
        ti.xcom_push(key=f'proyectos_{country}', value=proyectos)
        ti.xcom_push(key=f'total_{country}', value=total)
        
        return total
        
    except Exception as e:
        logger.error(f"❌ Error en extracción de {country}: {str(e)}")
        raise

