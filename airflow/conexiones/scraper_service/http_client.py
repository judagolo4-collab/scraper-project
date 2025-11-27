# http_client.py - Cliente para comunicarse con el Scraper Service

import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ScraperServiceClient:
    """Cliente para comunicarse con el servicio de scraping FastAPI"""
    
    def __init__(self, base_url: str = "http://scraper-api:8000"):
        """
        Inicializa el cliente
        
        :param base_url: URL base del servicio de scraping
        """
        self.base_url = base_url
        self.timeout = 300  # 5 minutos timeout para scraping
        
        logger.info(f"✅ ScraperServiceClient initialized (url: {base_url})")
    
    def health_check(self) -> bool:
        """
        Verifica que el servicio esté disponible
        
        :return: True si el servicio está disponible
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def scrape_country(
        self,
        country: str,
        institution: str,
        max_pages: Optional[int] = None,
        legislatura: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        classify: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta el scraping de un país/institución
        
        :param country: País (ej: 'colombia')
        :param institution: Institución (ej: 'camara')
        :param max_pages: Límite de páginas (opcional)
        :param legislatura: Filtro por legislatura (opcional)
        :param fecha_inicio: Fecha de inicio para carga incremental (DD-MM-YYYY)
        :param classify: Clasificar con Gemini AI
        :return: Dict con success, total_proyectos y proyectos
        """
        # Construir URL
        url = f"{self.base_url}/api/scrape/{country}/{institution}"
        
        # Parámetros
        params = {}
        if max_pages:
            params['max_pages'] = max_pages
        if legislatura:
            params['legislatura'] = legislatura
        if fecha_inicio:
            params['fecha_inicio'] = fecha_inicio
        params['classify'] = classify
        
        logger.info(f"🚀 Starting scraping: {country}/{institution}")
        if fecha_inicio:
            logger.info(f"📅 Incremental load from: {fecha_inicio}")
        
        # Hacer request
        try:
            response = requests.post(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"✅ Scraping completed: {data.get('total_proyectos', 0)} proyectos")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error("❌ Scraping timeout (> 5 min)")
            raise Exception("Scraping timeout")
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Error during scraping: {e}")
            raise
    
    def get_config(self, country: str) -> Dict[str, Any]:
        """
        Obtiene la configuración de un país
        
        :param country: País
        :return: Configuración
        """
        url = f"{self.base_url}/api/config/{country}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def list_sectores(self) -> List[str]:
        """
        Lista los sectores económicos disponibles
        
        :return: Lista de sectores
        """
        url = f"{self.base_url}/api/gemini/sectores"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('sectores', [])

