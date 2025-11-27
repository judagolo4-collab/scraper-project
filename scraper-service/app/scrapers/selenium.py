# selenium_scraper.py

from typing import List, Dict, Any, Tuple, Optional
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from .base import BaseScraper


class SeleniumScraper(BaseScraper):
    """
    Scraper para páginas con JavaScript dinámico.
    Usa Selenium + Chrome en modo headless (segundo plano).
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.selectors = config.get('selectors', {})
        self.wait_time = config.get('selenium', {}).get('wait_time', 10)
        self.driver = None
    
    def setup_driver(self):
        """Configurar driver de Selenium para ejecución headless."""
        from .user_agents import get_random_user_agent
        
        chrome_options = Options()
        
        # Opciones obligatorias para modo HEADLESS (sin ventana visible)
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # OPTIMIZACIONES para mayor velocidad
        chrome_options.add_argument('--disable-images')  # No cargar imágenes
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # Deshabilitar imágenes
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,  # No cargar imágenes
            "profile.default_content_setting_values.notifications": 2,  # No notificaciones
            "profile.managed_default_content_settings.stylesheets": 2,  # No CSS (opcional)
        })
        
        # User agent rotativo para evitar detección
        user_agent = get_random_user_agent()
        chrome_options.add_argument(f'user-agent={user_agent}')
        self.logger.debug(f"🎭 User-Agent: {user_agent[:50]}...")
        
        # Configuración del servicio
        try:
            import os
            # Priorizar variables de entorno sobre configuración
            chromium_path = os.environ.get('CHROME_BIN') or self.config.get('selenium', {}).get('chromium_path')
            if chromium_path:
                chrome_options.binary_location = chromium_path
                
            driver_path = os.environ.get('CHROMEDRIVER_PATH') or self.config.get('selenium', {}).get('driver_path', '/usr/bin/chromedriver')
            service = Service(driver_path)
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("✅ ChromeDriver iniciado en modo Headless.")
        except WebDriverException as e:
            self.logger.error(f"❌ Error iniciando ChromeDriver. Asegúrate de que el driver esté en '{driver_path}' y el binario de Chrome esté disponible. Error: {str(e)}")
            raise e
    
    def teardown_driver(self):
        """Cerrar driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("🛑 WebDriver cerrado.")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Método principal que debe ser implementado en la clase hija.
        Contiene la lógica base de navegación y paginación.
        """
        self.logger.error("⚠️ El método scrape() debe ser implementado en la clase hija para definir la lógica específica.")
        self.teardown_driver()
        return self.get_results()
            
    def wait_for_selector(self, selector: str, by: By = By.CSS_SELECTOR):
        """Esperar a que aparezca un selector."""
        self.logger.info(f"⏳ Esperando elemento: {selector}")
        wait = WebDriverWait(self.driver, self.wait_time)
        try:
            wait.until(
                EC.presence_of_element_located((by, selector))
            )
            self.logger.info(f"✅ Elemento encontrado")
        except TimeoutException:
            self.logger.error(f"❌ Timeout esperando el selector: {selector}")
            raise TimeoutException(f"El elemento '{selector}' no apareció después de {self.wait_time} segundos.")

    async def next_page(self, current_page: int) -> bool:
        """Navegar a la siguiente página según configuración (por URL o botón)."""
        pagination = self.config.get('pagination', {})
        if not pagination:
            return False
            
        # Estrategia 1: Parámetro en URL (ej: ?page=2)
        if 'param_name' in pagination:
            param = pagination['param_name']
            next_page = current_page + 1
            
            base_url = self.url.split('?')[0]
            separator = '&' if '?' in self.url else '?'
            next_url = f"{base_url}{separator}{param}={next_page}"
            
            self.logger.info(f"➡️  Navegando a URL: {next_url}")
            self.driver.get(next_url)
            await asyncio.sleep(2)
            return True
            
        # Estrategia 2: Botón 'Siguiente'
        elif 'next_button' in pagination:
            selector = pagination['next_button']
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                # Verificar si está deshabilitado
                if 'disabled' in btn.get_attribute('class') or btn.get_attribute('disabled'):
                    self.logger.info("📄 Última página alcanzada (botón deshabilitado)")
                    return False
                    
                self.logger.info("➡️  Click en botón siguiente")
                self.driver.execute_script("arguments[0].click();", btn) 
                await asyncio.sleep(pagination.get('click_delay', 2)) 
                return True
            except NoSuchElementException:
                self.logger.warning(f"El botón de paginación '{selector}' no fue encontrado.")
                return False
            except Exception as e:
                self.logger.error(f"Error al hacer click en el botón siguiente: {e}")
                return False
        
        return False
    
    async def scroll_page(self, max_scrolls: int = 5):
        """Hacer scroll para cargar contenido lazy-loaded."""
        scroll_pause = 1.5
        scroll_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        self.logger.info("⬇️ Iniciando scroll de página...")
        
        while scroll_count < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(scroll_pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                self.logger.info(f"✅ Scroll completado (altura fija en {last_height}px).")
                break
            
            last_height = new_height
            scroll_count += 1
        
        if scroll_count >= max_scrolls:
            self.logger.warning(f"⚠️ Límite de {max_scrolls} scrolls alcanzado.")
    
    # ====================================================================
    # MÉTODOS ESENCIALES DE EXTRACCIÓN
    # ====================================================================
    
    def find_element_safe(self, selector: str, by: By = By.CSS_SELECTOR, parent = None) -> Optional[Any]:
        """
        Busca un elemento de forma segura sin lanzar excepción.
        
        :param selector: Selector CSS/XPath
        :param by: Tipo de selector
        :param parent: Elemento padre (None = buscar desde driver)
        :return: WebElement o None si no se encuentra
        """
        try:
            return (parent or self.driver).find_element(by, selector)
        except NoSuchElementException:
            return None
    
    def find_elements_safe(self, selector: str, by: By = By.CSS_SELECTOR, parent = None) -> List[Any]:
        """
        Busca múltiples elementos de forma segura.
        
        :param selector: Selector CSS/XPath
        :param by: Tipo de selector
        :param parent: Elemento padre (None = buscar desde driver)
        :return: Lista de WebElements (vacía si no encuentra)
        """
        try:
            return (parent or self.driver).find_elements(by, selector)
        except NoSuchElementException:
            return []
    
    def extract_text_safe(self, selector: str, by: By = By.CSS_SELECTOR, parent = None, default: str = "") -> str:
        """
        Extrae texto de un elemento de forma segura.
        
        :param selector: Selector CSS/XPath
        :param by: Tipo de selector
        :param parent: Elemento padre
        :param default: Valor por defecto si no se encuentra
        :return: Texto extraído o default
        """
        element = self.find_element_safe(selector, by, parent)
        return element.text.strip() if element else default
    
    def extract_attribute_safe(self, selector: str, attribute: str, by: By = By.CSS_SELECTOR, parent = None, default: Any = None) -> Any:
        """
        Extrae un atributo de un elemento de forma segura.
        
        :param selector: Selector CSS/XPath
        :param attribute: Nombre del atributo (ej: 'href', 'class', 'id')
        :param by: Tipo de selector
        :param parent: Elemento padre
        :param default: Valor por defecto si no se encuentra
        :return: Valor del atributo o default
        """
        element = self.find_element_safe(selector, by, parent)
        return element.get_attribute(attribute) if element else default
    
    async def click_element_safe(self, selector: str, by: By = By.CSS_SELECTOR, use_js: bool = True, wait_after: float = 1.0) -> bool:
        """
        Hace click en un elemento de forma segura.
        
        :param selector: Selector CSS/XPath
        :param by: Tipo de selector
        :param use_js: Usar JavaScript para el click (más confiable)
        :param wait_after: Tiempo de espera después del click
        :return: True si tuvo éxito, False si no
        """
        try:
            element = self.find_element_safe(selector, by)
            if not element:
                return False
            
            if use_js:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                element.click()
            
            if wait_after:
                await asyncio.sleep(wait_after)
            
            return True
        except Exception as e:
            self.logger.error(f"Error haciendo click en '{selector}': {e}")
            return False
    
    async def handle_popup(self, accept_selector: str = None, close_selector: str = None, wait_time: float = 2.0) -> bool:
        """
        Maneja popups o modales que aparecen en la página (cookies, avisos, etc).
        
        :param accept_selector: Selector del botón de aceptar/cerrar
        :param close_selector: Selector alternativo para cerrar
        :param wait_time: Tiempo de espera antes de buscar el popup
        :return: True si se cerró el popup, False si no
        """
        try:
            await asyncio.sleep(wait_time)
            
            if accept_selector:
                return await self.click_element_safe(accept_selector, use_js=True)
            
            if close_selector:
                return await self.click_element_safe(close_selector, use_js=True)
            
            return False
        except Exception as e:
            self.logger.debug(f"No se encontró popup: {e}")
            return False
    
    # ====================================================================
    # MÉTODO LEGACY (mantener por compatibilidad)
    # ====================================================================
    
    def extract_link_and_type(self, element, selector_or_xpath: str, use_xpath: bool = False) -> Tuple[Optional[str], str]:
        """
        Extrae una URL de un elemento usando un selector CSS o XPath y clasifica su tipo.

        :param element: El WebElement de Selenium (el contenedor) donde buscar.
        :param selector_or_xpath: El selector CSS o la expresión XPath para encontrar el enlace (<a>).
        :param use_xpath: Si es True, el primer argumento se trata como una expresión XPath.
        :return: Una tupla (URL, Tipo), donde Tipo es 'pdf', 'web' o 'unknown'.
        """
        link_url = None
        link_type = 'unknown'

        try:
            # 1. Determinar el método de búsqueda
            by_method = By.XPATH if use_xpath else By.CSS_SELECTOR
            
            # 2. Encontrar el elemento <a>
            link_element = element.find_element(by_method, selector_or_xpath)
            link_url = link_element.get_attribute('href')
            
            if not link_url:
                self.logger.warning(f"⚠️ Enlace encontrado con selector '{selector_or_xpath}' pero sin atributo 'href'.")
                return None, 'unknown'

            # 3. Normalizar y clasificar la URL
            link_url = link_url.strip()
            link_text = link_element.text.lower()
            
            # Clasificación
            if link_url.lower().endswith('.pdf'):
                link_type = 'pdf'
            elif 'documento' in link_text or 'descargar' in link_text or 'ver documento' in link_text:
                link_type = 'pdf'
            elif link_url.startswith('http') or link_url.startswith('/'):
                link_type = 'web'
            
            self.logger.debug(f"Link extraído: {link_url}, Tipo: {link_type}")

        except NoSuchElementException:
            self.logger.debug(f"❓ Enlace no encontrado con selector/xpath: {selector_or_xpath}")
            return None, 'unknown'
        except Exception as e:
            self.logger.error(f"❌ Error al extraer enlace con selector '{selector_or_xpath}': {e}")
            return None, 'unknown'

        return link_url, link_type
