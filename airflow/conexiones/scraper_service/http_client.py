import requests
import logging
from typing import Dict, Any, Optional

class ScraperHttpClient:
    """Cliente HTTP para comunicarse con el Scraper Service"""
    
    def __init__(self, base_url: str = "http://scraper-api:8000"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def scrape_colombia(self, fecha_inicio: Optional[str] = None, max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Llama al endpoint de scraping de Colombia.
        
        :param fecha_inicio: Fecha de inicio (DD-MM-YYYY)
        :param max_pages: Límite de páginas
        :return: Respuesta JSON del scraper
        """
        endpoint = f"{self.base_url}/api/scrape/colombia"
        params = {}
        
        if fecha_inicio:
            params['fecha_inicio'] = fecha_inicio
        if max_pages:
            params['max_pages'] = max_pages
            
        try:
            self.logger.info(f"📡 Llamando a Scraper API: {endpoint} con params {params}")
            response = requests.post(endpoint, params=params, timeout=3600) # 1 hora timeout
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Error llamando a Scraper API: {e}")
            raise
