# peru.py - Scraper para el Congreso de la República del Perú

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from ...scrapers.html_scraper import HTMLScraper


class CongresoPeruScraper(HTMLScraper):
    """
    Scraper específico para el Congreso de la República del Perú.
    Hereda de HTMLScraper (httpx + BeautifulSoup).
    
    Extrae proyectos de ley desde:
    https://www2.congreso.gob.pe/Sicr/TraDocEstProc/CLProLey2011.nsf/
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        periodo_filter: Optional[str] = None,
        **kwargs
    ):
        super().__init__(config, **kwargs)
        self.periodo_filter = periodo_filter
        self.base_url = config.get('base_url', '')
        
        self.logger.info(f"🇵🇪 Iniciando scraper para Congreso de Perú")
        if self.periodo_filter:
            self.logger.info(f"📅 Filtro de período: {self.periodo_filter}")
        if self.max_pages:
            self.logger.info(f"📄 Máximo de páginas: {self.max_pages}")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Ejecuta el scraping completo del Congreso de Perú.
        """
        try:
            self.logger.info(f"🚀 Iniciando scraping de {self.config['url']}")
            
            # Obtener HTML
            html = await self.fetch_page()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Encontrar la tabla principal
            table = soup.find('table', {'border': '0', 'cellpadding': '2'})
            
            if not table:
                self.logger.warning("⚠️ No se encontró la tabla de proyectos")
                return self.get_results()
            
            # Obtener todas las filas
            rows = table.find_all('tr', valign='top')
            self.logger.info(f"📦 Filas encontradas: {len(rows)}")
            
            for row in rows:
                try:
                    project = self.parse_item(row)
                    
                    if project and project.get('numero'):
                        self.add_result(project)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error parseando fila: {str(e)}")
                    continue
            
            total = len(self.results)
            self.logger.info(f"🎉 Scraping completado: {total} proyectos extraídos")
            
            return self.get_results()
            
        except Exception as e:
            self.logger.error(f"❌ Error durante el scraping: {str(e)}")
            return self.get_results()
    
    def parse_item(self, element: BeautifulSoup) -> Dict[str, Any]:
        """
        Parsear un proyecto de ley peruano desde una fila de tabla.
        
        Estructura HTML esperada:
        <tr valign="top">
          <td><a href="...">05425/2015-PE</a></td>
          <td align="center">03/07/2018</td>
          <td align="center">07/26/2016</td>
          <td align="center">Presentado</td>
          <td>LEY DE CREACIÓN...</td>
        </tr>
        """
        project = {}
        
        try:
            cells = element.find_all('td')
            
            if len(cells) < 5:
                return project
            
            # En Perú, la primera celda puede tener contenido anidado (imágenes, espacios)
            # Buscar el link del proyecto dentro de las celdas
            numero = None
            url_detalle = None
            fecha_ult_reg = None
            fecha_pres = None
            estado = None
            titulo = None
            
            # Buscar todas las celdas con contenido significativo
            for i, cell in enumerate(cells):
                # Buscar link con el número del proyecto
                if not numero:
                    link = cell.find('a', href=True)
                    if link and '/2015-' in link.get_text():  # Los números tienen formato XXXXX/2015-XX
                        numero = link.get_text(strip=True)
                        href = link.get('href', '')
                        if href and not href.startswith('http'):
                            if href.startswith('/'):
                                url_detalle = f"{self.base_url}{href}"
                            else:
                                url_detalle = f"{self.base_url}/{href}"
                        else:
                            url_detalle = href
                
                # Las celdas con align="center" son las fechas y estado
                if cell.get('align') == 'center':
                    text = cell.get_text(strip=True)
                    if text and '/' in text:  # Es una fecha
                        if not fecha_ult_reg:
                            fecha_ult_reg = text
                        elif not fecha_pres:
                            fecha_pres = text
                    elif text and not estado:  # Es el estado
                        estado = text
                
                # La celda sin align y con texto largo es el título
                if not cell.get('align') and cell.get_text(strip=True):
                    text = cell.get_text(strip=True)
                    if len(text) > 20 and not text.startswith('05'):  # No es número
                        titulo = text
            
            project['numero'] = numero
            project['url_detalle'] = url_detalle
            project['fecha_ultima_reg'] = fecha_ult_reg
            project['fecha_presentacion'] = fecha_pres
            project['estado'] = estado
            project['titulo'] = titulo
            
            # Metadata adicional
            project['source'] = 'congreso_peru'
            project['country'] = 'peru'
            
            return project
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error parseando elemento: {str(e)}")
            return project
    

