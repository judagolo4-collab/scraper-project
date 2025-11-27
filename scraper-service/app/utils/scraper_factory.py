# scraper_factory.py - Factory para crear scrapers dinámicamente

from typing import Dict, Any, Optional, Type
from ..scrapers.base import BaseScraper


class ScraperFactory:
    """
    Factory para crear instancias de scrapers dinámicamente.
    Permite registrar scrapers y crearlos por país/institución.
    """
    
    def __init__(self):
        self._scrapers: Dict[str, Type[BaseScraper]] = {}
    
    def register(self, key: str, scraper_class: Type[BaseScraper]):
        """
        Registra un scraper en el factory.
        
        :param key: Identificador único (ej: 'colombia_camara', 'peru_congreso')
        :param scraper_class: Clase del scraper (debe heredar de BaseScraper)
        """
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError(f"El scraper {scraper_class.__name__} debe heredar de BaseScraper")
        
        self._scrapers[key.lower()] = scraper_class
    
    def create(
        self,
        key: str,
        config: Dict[str, Any],
        **kwargs
    ) -> BaseScraper:
        """
        Crea una instancia de scraper basado en la clave.
        
        :param key: Identificador del scraper (ej: 'colombia_camara')
        :param config: Configuración del scraper
        :param kwargs: Argumentos adicionales para el constructor del scraper
        :return: Instancia del scraper
        """
        key = key.lower()
        
        if key not in self._scrapers:
            raise ValueError(
                f"Scraper '{key}' no encontrado. Scrapers disponibles: {list(self._scrapers.keys())}"
            )
        
        scraper_class = self._scrapers[key]
        return scraper_class(config, **kwargs)
    
    def create_by_country(
        self,
        country: str,
        config: Dict[str, Any],
        use_ajax: bool = False,
        **kwargs
    ) -> BaseScraper:
        """
        Crea una instancia de scraper basado en país.
        
        :param country: Nombre del país (ej: 'colombia', 'peru')
        :param config: Configuración del scraper
        :param use_ajax: Si True, usa versión AJAX (más rápida) si está disponible
        :param kwargs: Argumentos adicionales
        :return: Instancia del scraper
        """
        # Mapeo de países a instituciones por defecto
        default_institutions = {
            'colombia': 'camara',
            'peru': 'congreso',
            # Agregar más países aquí
        }
        
        institution = default_institutions.get(country.lower(), 'camara')
        
        # Intentar versión AJAX si se solicita
        if use_ajax:
            ajax_key = f"{country.lower()}_{institution.lower()}_ajax"
            if ajax_key in self._scrapers:
                return self.create(ajax_key, config, **kwargs)
        
        # Usar versión normal (Selenium)
        key = f"{country.lower()}_{institution.lower()}"
        return self.create(key, config, **kwargs)
    
    def list_available(self) -> list[str]:
        """
        Lista todos los scrapers registrados.
        
        :return: Lista de identificadores de scrapers
        """
        return list(self._scrapers.keys())


# Instancia global del factory
scraper_factory = ScraperFactory()


# Auto-registro de scrapers disponibles
def register_scrapers():
    """Registra automáticamente todos los scrapers disponibles"""
    from ..dominios.camara.colombia import CamaraColumbiaScraper
    from ..dominios.camara.colombia_ajax import CamaraColombiaAjaxScraper
    from ..dominios.congreso.peru import CongresoPeruScraper
    
    # Registrar scrapers existentes
    scraper_factory.register('colombia_camara', CamaraColumbiaScraper)  # Selenium (lento pero completo)
    scraper_factory.register('colombia_camara_ajax', CamaraColombiaAjaxScraper)  # AJAX (10-20x más rápido)
    scraper_factory.register('peru_congreso', CongresoPeruScraper)  # Selenium
    
    # Aquí se pueden registrar más scrapers en el futuro:
    # scraper_factory.register('peru_congreso', PeruCongresoScraper)
    # scraper_factory.register('argentina_camara', ArgentinaCamaraScraper)


# Registrar scrapers al importar el módulo
register_scrapers()

