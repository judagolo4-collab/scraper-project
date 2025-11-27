# colombia_ajax.py - Scraper AJAX para Cámara de Representantes de Colombia

import asyncio
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from ...scrapers.ajax_scraper import AjaxScraper
from ...mappings.colombia_filters import (
    get_legislatura_id,
    get_tipo_ley_id,
    get_estado_ley_id,
    ORIGEN_LEY
)


class CamaraColombiaAjaxScraper(AjaxScraper):
    """
    Scraper AJAX para la Cámara de Representantes de Colombia.
    Usa el endpoint AJAX real (admin-ajax.php) para obtener datos en JSON.
    
    ⚡ VENTAJAS sobre Selenium:
    - 10-20x más rápido
    - Sin navegador headless
    - Respuestas JSON directas
    - Puede hacer peticiones concurrentes
    """
    
    def __init__(
        self, 
        config: Dict[str, Any],
        legislatura_filter: Optional[str] = None,
        max_pages: Optional[int] = None,
        per_page: int = 100,
        fecha_inicio: Optional[str] = None,  # Para compatibilidad con la API
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        origen: Optional[str] = None,
        comision: Optional[str] = None,
        **kwargs  # Ignorar otros parámetros
    ):
        super().__init__(config)
        
        # Usar URL base fija (no la del config que incluye el path completo)
        self.base_url = 'https://www.camara.gov.co'
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        self.main_page = f"{self.base_url}/proyectos-de-ley/"
        
        self.legislatura_filter = legislatura_filter
        self.max_pages = max_pages
        self.per_page = per_page
        self.fecha_inicio = fecha_inicio  # No se usa en AJAX pero se mantiene para compatibilidad
        
        # Filtros adicionales
        self.tipo_filter = tipo
        self.estado_filter = estado
        self.origen_filter = origen
        self.comision_filter = comision
        
        self._nonce_cache: Optional[str] = None
        
    async def _get_nonce(self) -> Optional[str]:
        """
        Extrae el nonce dinámico de la página principal.
        El nonce es necesario para hacer peticiones AJAX.
        
        Returns:
            Nonce string o None si falla
        """
        if self._nonce_cache:
            self.logger.debug(f"🔑 Usando nonce en cache: {self._nonce_cache}")
            return self._nonce_cache
        
        self.logger.info(f"🔑 Obteniendo nonce desde {self.main_page}")
        html = await self._get_html(self.main_page)
        
        if not html:
            self.logger.error("❌ No se pudo obtener HTML de la página principal")
            return None
        
        # Buscar: PL_NONCE:"e5a976f354"
        nonce = self._extract_from_html(html, r'PL_NONCE:"([a-f0-9]+)"')
        
        if nonce:
            self._nonce_cache = nonce
            self.logger.info(f"✅ Nonce obtenido: {nonce}")
        else:
            self.logger.error("❌ No se pudo extraer el nonce")
        
        return nonce
    
    async def _fetch_projects_page(
        self, 
        page: int, 
        legislatura_id: str = "All",
        tipo_id: str = "All",
        estado_id: str = "All",
        origen_id: str = "All",
        comision_id: str = "All"
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene una página de proyectos desde el endpoint AJAX.
        
        Args:
            page: Número de página (1-indexed)
            legislatura_id: ID de legislatura ("All", "3" para 2024-2025, etc.)
            tipo_id: ID de tipo de ley ("All", "1" para Ley Ordinaria, etc.)
            estado_id: ID de estado ("All", "1" para Trámite en Comisión, etc.)
            origen_id: ID de origen ("All", "1" para Cámara, "2" para Senado)
            comision_id: ID de comisión ("All", "1" para Primera, etc.)
            
        Returns:
            Dict con 'items', 'total', 'total_pages' o None si falla
        """
        nonce = await self._get_nonce()
        if not nonce:
            return None
        
        # Datos del formulario con todos los filtros
        form_data = {
            "action": "get_proyectos_ley_page",
            "_ajax_nonce": nonce,
            "page": str(page),
            "per_page": str(self.per_page),
            "term": "",
            "comision": "",
            "tipo": tipo_id,
            "estado": estado_id,
            "origen": origen_id,
            "legislatura": legislatura_id,
            "comision_adv": comision_id
        }
        
        self.logger.info(f"📄 Consultando página {page} (legislatura: {legislatura_id})")
        response = await self._post_ajax(self.ajax_url, form_data)
        
        if not response:
            return None
        
        if not response.get('success'):
            self.logger.warning(f"⚠️ Respuesta no exitosa: {response}")
            return None
        
        data = response.get('data', {})
        items = data.get('items', [])
        total = data.get('total', 0)
        total_pages = data.get('total_pages', 0)
        
        self.logger.info(f"✅ Página {page}: {len(items)} proyectos (total: {total}, páginas: {total_pages})")
        
        return {
            'items': items,
            'total': total,
            'total_pages': total_pages
        }
    
    async def _get_pdf_link(self, proyecto_slug: str) -> Optional[str]:
        """
        Extrae el enlace del PDF desde la página individual del proyecto.
        Usa el mismo método que funciona en notebook.
        
        Args:
            proyecto_slug: Slug del proyecto (ej: "ley-catastro-multiproposito")
            
        Returns:
            URL del PDF o None
        """
        if not proyecto_slug:
            return None
            
        url = f"{self.base_url}/{proyecto_slug}/"
        
        try:
            html = await self._get_html(url)
            
            if not html:
                self.logger.debug(f"⚠️ No se pudo obtener HTML de {url}")
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar enlace con texto "Ver Documento" (case insensitive)
            pdf_link = soup.find('a', string=re.compile(r'Ver Documento', re.IGNORECASE))
            if pdf_link and pdf_link.get('href'):
                href = pdf_link['href']
                self.logger.debug(f"✅ PDF encontrado (Ver Documento): {href[:80]}")
                return href
            
            # Alternativa: buscar cualquier link .pdf
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
            if pdf_links:
                href = pdf_links[0]['href']
                self.logger.debug(f"✅ PDF encontrado (link .pdf): {href[:80]}")
                return href
            
            self.logger.debug(f"⚠️ No se encontró PDF en {url}")
            
        except Exception as e:
            self.logger.debug(f"⚠️ Error extrayendo PDF de {url}: {str(e)}")
        
        return None
    
    def _transform_project(self, raw_project: Dict[str, Any], include_pdf: bool = False) -> Dict[str, Any]:
        """
        Transforma un proyecto de la API a nuestro formato estándar.
        
        Args:
            raw_project: Proyecto en formato de la API
            include_pdf: Si True, incluye el slug para extraer PDF después
            
        Returns:
            Proyecto en formato estándar
        """
        proyecto = {
            'numero_camara': raw_project.get('nro_camara', ''),
            'numero_senado': raw_project.get('nro_senado', ''),
            'titulo': raw_project.get('proyecto', ''),
            'titulo_completo': raw_project.get('titulo', ''),
            'url_detalle': f"{self.base_url}/{raw_project.get('link_web', '')}" if raw_project.get('link_web') else None,
            'tipo': raw_project.get('tipo', ''),
            'autores': raw_project.get('autores_pack', ''),
            'estado': raw_project.get('estado', ''),
            'origen': raw_project.get('origen', ''),
            'comision': raw_project.get('comisiones_pack', ''),
            'legislatura': raw_project.get('vigencia', ''),
            'fecha_radicacion': None,  # No disponible en la API
            'resumen': raw_project.get('titulo', ''),
            'url_pdf': None,  # Se obtiene después si es necesario
            'url_gaceta': None,  # No disponible en la API
        }
        
        # Guardar slug para extraer PDF después si se necesita
        if include_pdf:
            proyecto['_slug'] = raw_project.get('link_web', '')
        
        return proyecto
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Ejecuta el scraping usando el endpoint AJAX.
        
        Returns:
            Lista de proyectos extraídos
        """
        try:
            self.logger.info("🚀 Iniciando scraping AJAX de Colombia - Cámara de Representantes")
            self.logger.info(f"🔗 URL AJAX: {self.ajax_url}")
            
            # Convertir filtros a IDs
            legislatura_id = "All"
            if self.legislatura_filter:
                legislatura_id = get_legislatura_id(self.legislatura_filter)
                self.logger.info(f"🔍 Filtrando por legislatura: {self.legislatura_filter} (ID: {legislatura_id})")
            
            tipo_id = get_tipo_ley_id(self.tipo_filter) if self.tipo_filter else "All"
            estado_id = get_estado_ley_id(self.estado_filter) if self.estado_filter else "All"
            origen_id = self.origen_filter if self.origen_filter else "All"
            comision_id = self.comision_filter if self.comision_filter else "All"
            
            # Log de filtros aplicados
            filters_applied = []
            if tipo_id != "All":
                filters_applied.append(f"tipo={self.tipo_filter}")
            if estado_id != "All":
                filters_applied.append(f"estado={self.estado_filter}")
            if origen_id != "All":
                filters_applied.append(f"origen={self.origen_filter}")
            if comision_id != "All":
                filters_applied.append(f"comision={self.comision_filter}")
            
            if filters_applied:
                self.logger.info(f"🔍 Filtros adicionales: {', '.join(filters_applied)}")
            
            # Obtener primera página para conocer el total
            first_page = await self._fetch_projects_page(
                1, legislatura_id, tipo_id, estado_id, origen_id, comision_id
            )
            
            if not first_page:
                self.logger.error("❌ No se pudo obtener la primera página")
                return self.get_results()
            
            total_pages = first_page['total_pages']
            total_items = first_page['total']
            
            self.logger.info(f"📊 Total de páginas disponibles: {total_pages}")
            self.logger.info(f"📊 Total de proyectos disponibles: {total_items}")
            
            # Determinar cuántas páginas scrapear
            pages_to_fetch = total_pages
            if self.max_pages:
                pages_to_fetch = min(self.max_pages, total_pages)
                self.logger.info(f"⚠️ Límite de páginas configurado: {self.max_pages}")
            
            # Procesar primera página
            for item in first_page['items']:
                proyecto = self._transform_project(item, include_pdf=True)
                self.add_result(proyecto)
            
            # Procesar páginas restantes
            for page in range(2, pages_to_fetch + 1):
                self.logger.info(f"📄 Procesando página {page}/{pages_to_fetch}")
                
                page_data = await self._fetch_projects_page(
                    page, legislatura_id, tipo_id, estado_id, origen_id, comision_id
                )
                
                if not page_data:
                    self.logger.warning(f"⚠️ No se pudo obtener página {page}")
                    continue
                
                for item in page_data['items']:
                    proyecto = self._transform_project(item, include_pdf=True)
                    self.add_result(proyecto)
                
                # Delay para no saturar el servidor
                await asyncio.sleep(0.5)
            
            self.logger.info(f"✨ Scraping AJAX completado. Total: {len(self.get_results())} proyectos")
            
            # Extraer PDFs si hay proyectos (solo para los primeros proyectos para no tardar mucho)
            resultados = self.get_results()
            if resultados:
                self.logger.info(f"📄 Extrayendo enlaces PDF (máximo 20 proyectos)...")
                
                for idx, proyecto in enumerate(resultados[:20], 1):  # Limitar a 20 para no tardar
                    slug = proyecto.get('_slug')
                    if slug:
                        pdf_url = await self._get_pdf_link(slug)
                        proyecto['url_pdf'] = pdf_url
                        # Remover el slug temporal
                        proyecto.pop('_slug', None)
                        
                        if idx % 5 == 0:
                            self.logger.info(f"📄 Procesados {idx}/20 PDFs...")
                        
                        # Pequeño delay entre peticiones
                        await asyncio.sleep(0.3)
                
                self.logger.info(f"✅ Extracción de PDFs completada")
            
            return resultados
            
        except Exception as e:
            self.logger.error(f"❌ Error en scraping AJAX: {str(e)}", exc_info=True)
            return self.get_results()
        
        finally:
            await self._close_session()

