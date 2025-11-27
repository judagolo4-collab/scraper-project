# colombia.py - Scraper para Cámara de Representantes de Colombia

from typing import List, Dict, Any, Optional
import asyncio
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from ...scrapers.selenium import SeleniumScraper
from ...scrapers.helpers import DateParser, TextExtractor, LinkExtractor, TableExtractor


class CamaraColumbiaScraper(SeleniumScraper):
    """
    Scraper específico para la Cámara de Representantes de Colombia.
    Extrae proyectos de ley desde: https://www.camara.gov.co/secretaria/proyectos-de-ley
    """
    
    def __init__(
        self, 
        config: Dict[str, Any], 
        legislatura_filter: Optional[str] = None, 
        fecha_inicio: Optional[str] = None,
        max_pages: Optional[int] = None,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        origen: Optional[str] = None,
        comision: Optional[str] = None,
        **kwargs  # Ignorar otros parámetros
    ):
        """
        Inicializa el scraper de Colombia.
        
        :param config: Configuración del scraper
        :param legislatura_filter: Filtro opcional por legislatura (ej: "2023-2024")
        :param fecha_inicio: Filtro opcional por fecha de inicio (DD-MM-YYYY). 
                             Se detendrá el scraper al encontrar proyectos anteriores a esta fecha.
        :param max_pages: Límite de páginas (se ignora si config tiene limits.max_pages)
        :param tipo, estado, origen, comision: Filtros para compatibilidad (solo funcionan con AJAX)
        """
        super().__init__(config)
        self.legislatura_filter = legislatura_filter
        self.selectors = config.get('selectors', {})
        self.fecha_inicio = DateParser.parse_date(fecha_inicio) if fecha_inicio else None
        
        # Los filtros adicionales se ignoran en Selenium (solo funcionan con AJAX)
        # Pero los aceptamos para mantener compatibilidad de API
        
        if self.fecha_inicio:
            self.logger.info(f"📅 Filtro de fecha activo: Procesando proyectos desde {self.fecha_inicio.strftime('%d/%m/%Y')}")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Método principal de scraping.
        Itera por todas las páginas, extrae proyectos y navega a detalles.
        """
        try:
            self.setup_driver()
            self.logger.info(f"🚀 Iniciando scraping de Colombia - Cámara de Representantes")
            self.logger.info(f"🔗 URL: {self.url}")
            
            if self.legislatura_filter:
                self.logger.info(f"🔍 Filtro de legislatura: {self.legislatura_filter}")
            
            # Navegar a la URL principal
            self.driver.get(self.url)
            await asyncio.sleep(2)  # OPTIMIZADO: reducido de 3s a 2s
            
            # Esperar a que cargue la tabla
            self.wait_for_selector(self.selectors.get('tabla_proyectos', 'table tbody tr'))
            
            current_page = 1
            total_proyectos = 0
            max_pages = self.config.get('limits', {}).get('max_pages', None)
            
            if max_pages:
                self.logger.info(f"⚠️  Límite de páginas configurado: {max_pages}")
            
            while True:
                self.logger.info(f"📄 Procesando página {current_page}")
                
                # Extraer proyectos de la página actual
                try:
                    proyectos_en_pagina = await self._extract_projects_from_page()
                    total_proyectos += len(proyectos_en_pagina)
                    
                    self.logger.info(f"✅ Extraídos {len(proyectos_en_pagina)} proyectos de la página {current_page}")
                    self.logger.info(f"📊 Total acumulado: {total_proyectos} proyectos")
                except StopIteration:
                    self.logger.info("🏁 Deteniendo scraping por filtro de fecha.")
                    break
                
                # Verificar si se alcanzó el límite de páginas
                if max_pages and current_page >= max_pages:
                    self.logger.info(f"🏁 Límite de {max_pages} página(s) alcanzado. Scraping completado.")
                    break
                
                # Intentar ir a la siguiente página
                has_next = await self.next_page(current_page)
                
                if not has_next:
                    self.logger.info("🏁 No hay más páginas. Scraping completado.")
                    break
                
                current_page += 1
                await asyncio.sleep(1)  # OPTIMIZADO: reducido de 2s a 1s
            
            self.logger.info(f"✨ Scraping finalizado. Total de proyectos extraídos: {total_proyectos}")
            
        except Exception as e:
            self.logger.error(f"❌ Error durante el scraping: {str(e)}", exc_info=True)
        finally:
            self.teardown_driver()
        
        return self.get_results()
    
    async def _extract_projects_from_page(self) -> List[Dict[str, Any]]:
        """
        Extrae todos los proyectos de la página actual.
        OPTIMIZADO: Extrae HTML y procesa con BeautifulSoup para mayor velocidad.
        """
        proyectos = []
        
        try:
            # OPTIMIZACIÓN: Extraer HTML completo de una vez con BeautifulSoup
            from bs4 import BeautifulSoup
            page_html = self.driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Buscar tabla por ID o clase
            table = soup.find('table', id='listado-pley')
            if not table:
                table = soup.select_one('table.listado-pley')
            if not table:
                # Fallback: buscar primera tabla disponible
                all_tables = soup.find_all('table')
                table = all_tables[0] if all_tables else None
            
            if not table:
                self.logger.warning("⚠️ No se encontró la tabla de proyectos")
                return proyectos
            
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else []
            self.logger.info(f"🔍 Encontradas {len(rows)} filas en la tabla")
            
            # Guardar referencia al driver para páginas de detalle
            original_window = self.driver.current_window_handle
            
            for idx, row in enumerate(rows, 1):
                try:
                    # Extraer datos básicos de la fila (ahora con BeautifulSoup)
                    proyecto_data = self._extract_row_data_bs4(row)
                    
                    # Aplicar filtro de legislatura si existe
                    if self.legislatura_filter:
                        legislatura = proyecto_data.get('legislatura', '')
                        if self.legislatura_filter.lower() not in legislatura.lower():
                            self.logger.debug(f"⏭️  Proyecto {idx} omitido por filtro de legislatura")
                            continue
                    
                    # Obtener el enlace de detalle
                    detalle_url = proyecto_data.get('url_detalle')
                    
                    if detalle_url:
                        # OPTIMIZACIÓN: Navegar a detalle solo si es necesario
                        detalle_data = await self._extract_detail_page(detalle_url)
                        proyecto_data.update(detalle_data)
                        
                        # Volver a la ventana original
                        try:
                            self.driver.switch_to.window(original_window)
                        except:
                            pass
                        
                        # Verificar filtro de fecha
                        if self.fecha_inicio and proyecto_data.get('fecha_radicacion'):
                            fecha_rad = DateParser.parse_date(proyecto_data['fecha_radicacion'])
                            if fecha_rad and fecha_rad < self.fecha_inicio:
                                self.logger.info(f"🛑 Proyecto con fecha {fecha_rad.strftime('%d/%m/%Y')} es anterior al filtro {self.fecha_inicio.strftime('%d/%m/%Y')}. Deteniendo scraping.")
                                raise StopIteration("Fecha límite alcanzada")
                    
                    # Agregar el proyecto a los resultados
                    self.add_result(proyecto_data)
                    proyectos.append(proyecto_data)
                    
                    self.logger.info(f"✅ Proyecto {idx}/{len(rows)}: {proyecto_data.get('titulo', 'N/A')[:50]}...")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error procesando fila {idx}: {str(e)}")
                    continue
        
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo proyectos de la página: {str(e)}")
        
        return proyectos
    
    def _extract_row_data(self, row) -> Dict[str, Any]:
        """
        Extrae los datos básicos de una fila de la tabla.
        
        Columnas esperadas:
        - No. Cámara
        - No. Senado
        - Proyecto (con enlace "Ver detalle")
        - Tipo
        - Autores
        - Estado
        - Origen
        - Comisión
        - Legislatura
        """
        data = {}
        
        try:
            cells = row.find_elements(By.TAG_NAME, 'td')
            
            if len(cells) >= 9:
                data['numero_camara'] = cells[0].text.strip()
                data['numero_senado'] = cells[1].text.strip()
                
                # Extraer título y URL de detalle
                proyecto_cell = cells[2]
                data['titulo'] = proyecto_cell.text.strip().replace('Ver detalle', '').strip()
                
                try:
                    link = proyecto_cell.find_element(By.TAG_NAME, 'a')
                    data['url_detalle'] = link.get_attribute('href')
                except NoSuchElementException:
                    data['url_detalle'] = None
                    self.logger.warning("⚠️ No se encontró enlace de detalle")
                
                data['tipo'] = cells[3].text.strip()
                data['autores'] = cells[4].text.strip()
                data['estado'] = cells[5].text.strip()
                data['origen'] = cells[6].text.strip()
                data['comision'] = cells[7].text.strip()
                data['legislatura'] = cells[8].text.strip()
            else:
                self.logger.warning(f"⚠️ Fila con número inesperado de columnas: {len(cells)}")
        
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos de fila: {str(e)}")
        
        return data
    
    def _extract_row_data_bs4(self, row) -> Dict[str, Any]:
        """
        Extrae datos de una fila usando BeautifulSoup (más rápido).
        """
        cells = row.find_all('td')
        data = {}
        
        if len(cells) >= 9:
            data['numero_camara'] = cells[0].get_text(strip=True)
            data['numero_senado'] = cells[1].get_text(strip=True)
            
            # Extraer título y URL
            titulo_cell = cells[2]
            data['titulo'] = titulo_cell.get_text(strip=True).replace('Ver detalle', '').strip()
            
            link = titulo_cell.find('a')
            data['url_detalle'] = link.get('href') if link and link.has_attr('href') else None
            
            data['tipo'] = cells[3].get_text(strip=True)
            data['autores'] = cells[4].get_text(strip=True)
            data['estado'] = cells[5].get_text(strip=True)
            data['origen'] = cells[6].get_text(strip=True)
            data['comision'] = cells[7].get_text(strip=True)
            data['legislatura'] = cells[8].get_text(strip=True)
        else:
            self.logger.warning(f"⚠️ Fila con columnas inesperadas: {len(cells)}")
        
        return data
    
    async def _extract_detail_page(self, url: str) -> Dict[str, Any]:
        """
        Navega a la página de detalle y extrae información adicional.
        
        Información a extraer:
        - Fecha de radicación
        - Objeto del proyecto (resumen/exposición de motivos)
        - Enlace al PDF del proyecto
        - Enlace a la Gaceta
        """
        detail_data = {}
        original_window = self.driver.current_window_handle
        
        try:
            # Abrir enlace en nueva pestaña
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            await asyncio.sleep(1)  # OPTIMIZADO: reducido de 2s a 1s
            
            # Cambiar a la nueva pestaña
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[-1])
            
            # Esperar a que cargue el contenido
            await asyncio.sleep(1)  # OPTIMIZADO: reducido de 2s a 1s
            
            # Obtener el texto completo de la página
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Extraer fecha de radicación usando helper
            fecha = TextExtractor.extract_text_from_lines(page_text, 'Fecha de Radicación', lines_after=1)
            if fecha:
                fecha_match = DateParser.extract_date_from_text(fecha)
                detail_data['fecha_radicacion'] = fecha_match
            else:
                detail_data['fecha_radicacion'] = None
            
            # Extraer resumen/título usando helper
            resumen = TextExtractor.extract_text_from_lines(page_text, 'Título', lines_after=1)
            detail_data['resumen'] = resumen
            
            # Extraer enlace al PDF usando helper
            pdf_url, _ = LinkExtractor.extract_link(
                self.driver,
                'div.pl-pub-item a[href*=".pdf"]',
                By.CSS_SELECTOR
            )
            
            if not pdf_url:
                # Intentar selector alternativo
                pdf_url, _ = LinkExtractor.extract_link(
                    self.driver,
                    "//a[contains(text(), 'Ver Documento')]",
                    By.XPATH
                )
            
            detail_data['url_pdf'] = pdf_url
            
            # Extraer enlace a la Gaceta usando helper
            gaceta_url, _ = LinkExtractor.extract_link(
                self.driver,
                "//a[contains(text(), 'Gaceta')]",
                By.XPATH
            )
            detail_data['url_gaceta'] = gaceta_url
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo detalles de {url}: {str(e)}")
        finally:
            # Cerrar la pestaña y volver a la original
            try:
                self.driver.close()
                self.driver.switch_to.window(original_window)
            except:
                pass
        
        return detail_data
