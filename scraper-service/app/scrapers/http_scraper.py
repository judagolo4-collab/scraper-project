# http_scraper.py - Scraper base usando HTTP requests (más rápido que Selenium)

from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from .base import BaseScraper
from .user_agents import get_random_user_agent


class HTTPScraper(BaseScraper):
    """
    Scraper optimizado que usa HTTP requests + BeautifulSoup.
    Mucho más rápido que Selenium (no requiere navegador).
    
    Ventajas:
    - 10-20x más rápido que Selenium
    - Menos recursos (sin Chrome headless)
    - Más confiable para sitios sin JavaScript pesado
    
    Usar cuando:
    - El sitio NO requiere JavaScript para cargar contenido
    - El HTML está completo en la respuesta inicial
    - No hay paginación con JavaScript
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def _create_session(self):
        """Crear sesión HTTP con headers apropiados"""
        if not self.session:
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout
            )
            self.logger.info("✅ Sesión HTTP creada")
    
    async def _close_session(self):
        """Cerrar sesión HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("🛑 Sesión HTTP cerrada")
    
    async def fetch_html(self, url: str, retries: int = 3) -> Optional[str]:
        """
        Obtiene el HTML de una URL con reintentos.
        
        :param url: URL a solicitar
        :param retries: Número de reintentos en caso de error
        :return: HTML como string o None si falla
        """
        await self._create_session()
        
        for attempt in range(retries):
            try:
                self.logger.info(f"🌐 Solicitando: {url} (intento {attempt + 1}/{retries})")
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        self.logger.info(f"✅ HTML obtenido ({len(html)} bytes)")
                        return html
                    else:
                        self.logger.warning(f"⚠️ Status {response.status} para {url}")
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"⏰ Timeout en intento {attempt + 1}")
            except Exception as e:
                self.logger.error(f"❌ Error en intento {attempt + 1}: {str(e)}")
            
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Backoff exponencial
                self.logger.info(f"⏳ Esperando {wait_time}s antes de reintentar...")
                await asyncio.sleep(wait_time)
        
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parsea HTML con BeautifulSoup.
        
        :param html: String con HTML
        :return: Objeto BeautifulSoup
        """
        return BeautifulSoup(html, 'html.parser')
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Método principal que debe ser implementado en la clase hija.
        """
        self.logger.error("⚠️ El método scrape() debe ser implementado en la clase hija.")
        await self._close_session()
        return self.get_results()
    
    # ====================================================================
    # MÉTODOS HELPER PARA EXTRACCIÓN
    # ====================================================================
    
    def find_element(self, soup: BeautifulSoup, selector: str, **kwargs) -> Optional[Any]:
        """
        Busca un elemento en el HTML parseado.
        
        :param soup: BeautifulSoup object
        :param selector: Selector CSS
        :param kwargs: Argumentos adicionales para find()
        :return: Elemento encontrado o None
        """
        try:
            return soup.select_one(selector, **kwargs)
        except Exception as e:
            self.logger.debug(f"Elemento no encontrado con selector '{selector}': {e}")
            return None
    
    def find_elements(self, soup: BeautifulSoup, selector: str, **kwargs) -> List[Any]:
        """
        Busca múltiples elementos en el HTML parseado.
        
        :param soup: BeautifulSoup object
        :param selector: Selector CSS
        :param kwargs: Argumentos adicionales para select()
        :return: Lista de elementos (vacía si no encuentra)
        """
        try:
            return soup.select(selector, **kwargs)
        except Exception as e:
            self.logger.debug(f"Elementos no encontrados con selector '{selector}': {e}")
            return []
    
    def extract_text(self, element, default: str = "") -> str:
        """
        Extrae texto de un elemento de forma segura.
        
        :param element: Elemento BeautifulSoup
        :param default: Valor por defecto si no hay texto
        :return: Texto extraído
        """
        if element:
            text = element.get_text(strip=True)
            return text if text else default
        return default
    
    def extract_attribute(self, element, attribute: str, default: Any = None) -> Any:
        """
        Extrae un atributo de un elemento de forma segura.
        
        :param element: Elemento BeautifulSoup
        :param attribute: Nombre del atributo
        :param default: Valor por defecto
        :return: Valor del atributo
        """
        if element and element.has_attr(attribute):
            return element[attribute]
        return default
    
    async def fetch_multiple_urls(self, urls: List[str], max_concurrent: int = 5) -> List[Optional[str]]:
        """
        Obtiene múltiples URLs de forma concurrente.
        
        :param urls: Lista de URLs a solicitar
        :param max_concurrent: Máximo de requests concurrentes
        :return: Lista de HTMLs (None si falló alguna)
        """
        await self._create_session()
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return await self.fetch_html(url, retries=2)
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convertir excepciones en None
        return [r if isinstance(r, str) else None for r in results]

