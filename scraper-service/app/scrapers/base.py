# base.py

from typing import List, Dict, Any
import logging
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    Clase Abstracta Base para todos los Scrapers.
    Define la estructura mínima y maneja la configuración común,
    el logging y los resultados estandarizados.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el scraper base.

        :param config: Diccionario de configuración general.
        """
        self.config = config
        self.results: List[Dict[str, Any]] = []
        self.logger = self._setup_logging()
        self.url = config.get('url', 'N/A')
    
    def _setup_logging(self) -> logging.Logger:
        """Configura y retorna el logger específico para el scraper."""
        logger_name = self.__class__.__name__
        logger = logging.getLogger(logger_name)
        
        # Obtener nivel de logging de la configuración, por defecto INFO
        log_level = self.config.get('log_level', 'INFO').upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Evitar añadir múltiples handlers si ya existen
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - [%(levelname)s] - {logger_name} - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Método principal abstracto que debe ser implementado
        por las clases hijas. Contiene la lógica de scraping.
        """
        pass
    
    def add_result(self, data: Dict[str, Any]):
        """
        Añade un resultado estandarizado (diccionario) a la lista de resultados.
        
        :param data: Diccionario con la información extraída de un ítem.
        """
        if data:
            self.results.append(data)
            self.logger.debug(f"Resultado añadido: {data.keys()}")
            
    def get_results(self) -> List[Dict[str, Any]]:
        """
        Retorna la lista completa de resultados estandarizados.
        """
        return self.results
