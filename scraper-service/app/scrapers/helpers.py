# helpers.py - Funciones helper reutilizables para todos los scrapers

from datetime import datetime
from typing import Optional, Tuple
import re
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import logging

logger = logging.getLogger(__name__)


class DateParser:
    """Utilidades para parsear fechas en diferentes formatos"""
    
    @staticmethod
    def parse_date(date_str: str, formats: list = None) -> Optional[datetime]:
        """
        Convierte string de fecha a datetime probando múltiples formatos.
        
        :param date_str: String con la fecha
        :param formats: Lista de formatos a probar (por defecto varios formatos comunes)
        :return: Objeto datetime o None si no se pudo parsear
        """
        if not date_str:
            return None
        
        # Normalizar separadores
        date_str = date_str.strip()
        
        # Formatos comunes en América Latina
        if formats is None:
            formats = [
                '%d/%m/%Y',      # DD/MM/YYYY
                '%d-%m-%Y',      # DD-MM-YYYY
                '%Y-%m-%d',      # YYYY-MM-DD (ISO)
                '%d.%m.%Y',      # DD.MM.YYYY
                '%d %m %Y',      # DD MM YYYY
                '%Y/%m/%d',      # YYYY/MM/DD
            ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"No se pudo parsear la fecha: {date_str}")
        return None
    
    @staticmethod
    def extract_date_from_text(text: str, pattern: str = None) -> Optional[str]:
        """
        Extrae una fecha de un texto usando expresiones regulares.
        
        :param text: Texto donde buscar la fecha
        :param pattern: Patrón regex personalizado (por defecto DD/MM/YYYY)
        :return: String con la fecha encontrada o None
        """
        if pattern is None:
            # Patrón para DD/MM/YYYY o DD-MM-YYYY
            pattern = r'\d{2}[/-]\d{2}[/-]\d{4}'
        
        match = re.search(pattern, text)
        return match.group(0) if match else None


class TextExtractor:
    """Utilidades para extraer texto de elementos web"""
    
    @staticmethod
    def extract_text(element: WebElement, selector: str, by: By = By.CSS_SELECTOR) -> Optional[str]:
        """
        Extrae texto de un elemento hijo usando un selector.
        
        :param element: Elemento padre
        :param selector: Selector CSS o XPath
        :param by: Tipo de selector (CSS_SELECTOR o XPATH)
        :return: Texto extraído o None
        """
        try:
            child = element.find_element(by, selector)
            return child.text.strip()
        except NoSuchElementException:
            return None
        except Exception as e:
            logger.debug(f"Error extrayendo texto con selector '{selector}': {e}")
            return None
    
    @staticmethod
    def extract_text_from_lines(text: str, keyword: str, lines_after: int = 1) -> Optional[str]:
        """
        Extrae texto que aparece N líneas después de una palabra clave.
        Útil para páginas de detalle con formato estructurado.
        
        :param text: Texto completo
        :param keyword: Palabra clave a buscar
        :param lines_after: Número de líneas después de la palabra clave
        :return: Texto encontrado o None
        """
        if keyword not in text:
            return None
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if keyword in line:
                target_index = i + lines_after
                if target_index < len(lines):
                    return lines[target_index].strip()
        
        return None


class LinkExtractor:
    """Utilidades para extraer y clasificar enlaces"""
    
    @staticmethod
    def extract_link(
        element: WebElement,
        selector: str,
        by: By = By.CSS_SELECTOR
    ) -> Tuple[Optional[str], str]:
        """
        Extrae una URL de un elemento y clasifica su tipo.
        
        :param element: Elemento contenedor
        :param selector: Selector CSS o XPath
        :param by: Tipo de selector
        :return: Tupla (URL, tipo) donde tipo es 'pdf', 'web' o 'unknown'
        """
        try:
            link_element = element.find_element(by, selector)
            url = link_element.get_attribute('href')
            
            if not url:
                return None, 'unknown'
            
            url = url.strip()
            link_text = link_element.text.lower()
            
            # Clasificar tipo de enlace
            link_type = LinkExtractor._classify_link(url, link_text)
            
            return url, link_type
            
        except NoSuchElementException:
            return None, 'unknown'
        except Exception as e:
            logger.debug(f"Error extrayendo enlace con selector '{selector}': {e}")
            return None, 'unknown'
    
    @staticmethod
    def _classify_link(url: str, text: str = "") -> str:
        """
        Clasifica un enlace según su URL o texto.
        
        :param url: URL del enlace
        :param text: Texto del enlace
        :return: Tipo de enlace ('pdf', 'web', 'doc', 'unknown')
        """
        url_lower = url.lower()
        text_lower = text.lower()
        
        # PDFs
        if url_lower.endswith('.pdf'):
            return 'pdf'
        if any(keyword in text_lower for keyword in ['pdf', 'documento', 'descargar', 'ver documento']):
            return 'pdf'
        
        # Documentos Word/Excel
        if any(ext in url_lower for ext in ['.doc', '.docx', '.xls', '.xlsx']):
            return 'doc'
        
        # Enlaces web
        if url.startswith('http') or url.startswith('/'):
            return 'web'
        
        return 'unknown'


class TableExtractor:
    """Utilidades para extraer datos de tablas HTML"""
    
    @staticmethod
    def extract_row_cells(row: WebElement, cell_tag: str = 'td') -> list[str]:
        """
        Extrae el texto de todas las celdas de una fila.
        
        :param row: Elemento <tr> de la tabla
        :param cell_tag: Tag de las celdas ('td' o 'th')
        :return: Lista con el texto de cada celda
        """
        try:
            cells = row.find_elements(By.TAG_NAME, cell_tag)
            return [cell.text.strip() for cell in cells]
        except Exception as e:
            logger.error(f"Error extrayendo celdas de fila: {e}")
            return []
    
    @staticmethod
    def extract_row_dict(
        row: WebElement,
        column_mapping: dict,
        cell_tag: str = 'td'
    ) -> dict:
        """
        Extrae datos de una fila y los convierte en un diccionario.
        
        :param row: Elemento <tr> de la tabla
        :param column_mapping: Mapeo de índice de columna a nombre de campo
                               Ej: {0: 'numero', 1: 'titulo', 2: 'fecha'}
        :param cell_tag: Tag de las celdas
        :return: Diccionario con los datos extraídos
        """
        cells = TableExtractor.extract_row_cells(row, cell_tag)
        data = {}
        
        for index, field_name in column_mapping.items():
            if index < len(cells):
                data[field_name] = cells[index]
            else:
                data[field_name] = None
        
        return data


class URLNormalizer:
    """Utilidades para normalizar y validar URLs"""
    
    @staticmethod
    def normalize_url(url: str, base_url: str = None) -> str:
        """
        Normaliza una URL, convirtiéndola en absoluta si es relativa.
        
        :param url: URL a normalizar
        :param base_url: URL base para URLs relativas
        :return: URL normalizada
        """
        if not url:
            return url
        
        url = url.strip()
        
        # Si ya es absoluta, retornarla
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # Si es relativa y tenemos base_url, convertirla en absoluta
        if base_url and url.startswith('/'):
            from urllib.parse import urljoin
            return urljoin(base_url, url)
        
        return url
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Valida si una URL tiene formato correcto.
        
        :param url: URL a validar
        :return: True si es válida, False en caso contrario
        """
        if not url:
            return False
        
        # Patrón básico de validación de URL
        pattern = re.compile(
            r'^https?://'  # http:// o https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # puerto opcional
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        return bool(pattern.match(url))

