# ajax_scraper.py - Scraper base para endpoints AJAX/REST

import asyncio
import aiohttp
import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from .base import BaseScraper


class AjaxScraper(BaseScraper):
    """
    Scraper base para sitios que exponen endpoints AJAX/REST.
    Mucho más rápido que Selenium porque hace peticiones HTTP directas.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea una sesión HTTP asíncrona."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=self.timeout
            )
            self.logger.info("✅ Sesión HTTP creada")
        return self.session
    
    async def _close_session(self):
        """Cierra la sesión HTTP."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("🛑 Sesión HTTP cerrada")
    
    async def _get_html(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Realiza una petición GET y retorna el HTML.
        
        Args:
            url: URL a consultar
            max_retries: Número máximo de reintentos
            
        Returns:
            HTML como string o None si falla
        """
        session = await self._get_session()
        
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"🌐 GET {url} (intento {attempt}/{max_retries})")
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        self.logger.info(f"✅ HTML obtenido ({len(html)} bytes)")
                        return html
                    else:
                        self.logger.warning(f"⚠️ Status {response.status}")
            except Exception as e:
                self.logger.error(f"❌ Error en intento {attempt}: {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
        
        return None
    
    async def _post_ajax(
        self, 
        url: str, 
        data: Dict[str, Any], 
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza una petición POST AJAX y retorna JSON.
        
        Args:
            url: URL del endpoint AJAX
            data: Datos a enviar (se convertirán a form data)
            max_retries: Número máximo de reintentos
            
        Returns:
            Respuesta JSON como dict o None si falla
        """
        session = await self._get_session()
        
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"📡 POST AJAX {url} (intento {attempt}/{max_retries})")
                self.logger.debug(f"📦 Datos: {data}")
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        self.logger.info(f"✅ JSON obtenido")
                        return json_data
                    else:
                        self.logger.warning(f"⚠️ Status {response.status}")
                        text = await response.text()
                        self.logger.debug(f"Response: {text[:200]}")
            except Exception as e:
                self.logger.error(f"❌ Error en intento {attempt}: {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    def _extract_from_html(
        self, 
        html: str, 
        pattern: str, 
        group: int = 1
    ) -> Optional[str]:
        """
        Extrae un valor del HTML usando regex.
        
        Args:
            html: HTML como string
            pattern: Patrón regex
            group: Grupo a extraer (default: 1)
            
        Returns:
            Valor extraído o None
        """
        match = re.search(pattern, html)
        if match:
            value = match.group(group)
            self.logger.debug(f"✅ Extraído: {value}")
            return value
        else:
            self.logger.warning(f"⚠️ No se encontró patrón: {pattern}")
            return None
    
    def _extract_from_soup(
        self, 
        soup: BeautifulSoup, 
        selector: str, 
        attribute: Optional[str] = None
    ) -> Optional[str]:
        """
        Extrae un valor usando BeautifulSoup.
        
        Args:
            soup: Objeto BeautifulSoup
            selector: Selector CSS
            attribute: Atributo a extraer (None para texto)
            
        Returns:
            Valor extraído o None
        """
        element = soup.select_one(selector)
        if element:
            if attribute:
                value = element.get(attribute)
            else:
                value = element.get_text(strip=True)
            self.logger.debug(f"✅ Extraído de '{selector}': {value}")
            return value
        else:
            self.logger.warning(f"⚠️ No se encontró selector: {selector}")
            return None
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Método principal de scraping. Debe ser implementado por las clases hijas.
        """
        self.logger.error("⚠️ El método scrape() debe ser implementado en la clase hija")
        return self.get_results()
    
    async def __aenter__(self):
        """Context manager para usar con 'async with'."""
        await self._get_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra la sesión al salir del context manager."""
        await self._close_session()

