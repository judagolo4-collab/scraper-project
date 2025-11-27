"""
Scraper para HTML estático usando httpx + BeautifulSoup
"""

from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
import asyncio

from .base import BaseScraper


class HTMLScraper(BaseScraper):
    """
    Scraper para páginas HTML estáticas.
    Usa httpx + BeautifulSoup (más rápido y ligero que Selenium).
    """
    
    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(config)
        self.url = config.get('url')
        self.selectors = config.get('selectors', {})
        self.timeout = config.get('limits', {}).get('timeout', 30)
        self.max_pages = kwargs.get('max_pages') or config.get('limits', {}).get('max_pages', 1)
        
        # Headers para evitar bloqueos
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    async def fetch_page(self, url: str = None) -> str:
        """
        Obtener contenido HTML de la página.
        
        Args:
            url: URL a scrapear (usa self.url si no se especifica)
            
        Returns:
            HTML como string
        """
        url = url or self.url
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                self.logger.info(f"🌐 Fetching: {url}")
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.text
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching page: {str(e)}")
            raise
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrapear página HTML (debe ser implementado por subclases).
        """
        html = await self.fetch_page()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Selector del contenedor de items
        container_selector = self.selectors.get('container')
        items = []
        
        if container_selector:
            elements = soup.select(container_selector)
            self.logger.info(f"📦 Elementos encontrados: {len(elements)}")
            
            for element in elements:
                try:
                    # Filtrar filas vacías o de encabezado
                    if element.name == 'tr':
                        cells = element.find_all('td')
                        if not cells or len(cells) == 0:
                            continue
                    
                    item = self.parse_item(element)
                    
                    # Validar que el item tenga al menos un campo importante
                    if item.get('numero') or item.get('titulo'):
                        items.append(item)
                        self.add_result(item)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error parseando elemento: {str(e)}")
                    continue
        
        return items
    
    def parse_item(self, element: BeautifulSoup) -> Dict[str, Any]:
        """
        Parsear un elemento HTML (debe ser implementado por subclases).
        
        Args:
            element: Elemento BeautifulSoup
            
        Returns:
            Diccionario con datos parseados
        """
        item = {}
        
        # Parsear cada campo según selectores
        for field, selector in self.selectors.items():
            if field == 'container':
                continue
            
            try:
                el = element.select_one(selector)
                if el:
                    # Si es un link, extraer href
                    if field.endswith('_url') or field.endswith('_link') or field == 'url_detalle':
                        href = el.get('href', '')
                        # Normalizar URL si es relativa
                        if href and not href.startswith('http'):
                            base_url = self.config.get('base_url', '')
                            if href.startswith('/'):
                                item[field] = f"{base_url}{href}"
                            else:
                                item[field] = f"{base_url}/{href}"
                        else:
                            item[field] = href
                    else:
                        item[field] = el.get_text(strip=True)
                else:
                    item[field] = None
            except Exception as e:
                self.logger.debug(f"⚠️ Error extrayendo '{field}': {str(e)}")
                item[field] = None
        
        return item

