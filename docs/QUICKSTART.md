# 🚀 QUICKSTART - Guía Rápida de Desarrollo

## 📖 Tabla de Contenidos

- [Levantar el Proyecto](#levantar-el-proyecto)
- [Agregar un Nuevo Scraper](#agregar-un-nuevo-scraper)
- [Probar tu Scraper](#probar-tu-scraper)
- [Helpers Disponibles](#helpers-disponibles)
- [Debugging](#debugging)

---

## Levantar el Proyecto

### Opción 1: Local (Desarrollo)

```bash
# 1. Ir al directorio del servicio
cd scraper-service

# 2. Activar entorno virtual
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias (si no lo has hecho)
pip install -r requirements.txt

# 4. Levantar servidor
uvicorn app.main:app --reload --port 8000

# 5. Abrir documentación interactiva
# http://localhost:8000/docs
```

### Opción 2: Docker

```bash
cd docker
docker-compose up --build
```

---

## Agregar un Nuevo Scraper

### Paso 1: Crear Archivo de Configuración

Crea `config/nuevo_pais.json`:

```json
{
  "pais": "NuevoPais",
  "institucion": "Congreso",
  "url": "https://congreso.nuevopais.gov/proyectos",
  "selenium": {
    "wait_time": 10,
    "driver_path": "/opt/homebrew/bin/chromedriver"
  },
  "selectors": {
    "tabla_proyectos": "table.proyectos tbody tr",
    "paginacion_siguiente": "button.next-page"
  },
  "pagination": {
    "next_button": "button.next-page",
    "click_delay": 2
  },
  "limits": {
    "max_pages": null,
    "request_delay": 1
  },
  "log_level": "INFO"
}
```

### Paso 2: Crear Clase del Scraper

Crea `app/dominios/congreso/nuevo_pais.py`:

```python
# nuevo_pais.py - Scraper para Congreso de NuevoPais

from typing import List, Dict, Any, Optional
import asyncio
from selenium.webdriver.common.by import By
from ...scrapers.selenium import SeleniumScraper
from ...scrapers.helpers import (
    DateParser,
    TextExtractor,
    LinkExtractor,
    TableExtractor
)


class CongresoNuevoPaisScraper(SeleniumScraper):
    """
    Scraper para el Congreso de NuevoPais.
    """
    
    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(config)
        self.selectors = config.get('selectors', {})
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Método principal de scraping"""
        try:
            self.setup_driver()
            self.logger.info(f"🚀 Iniciando scraping de {self.config['pais']}")
            
            # Navegar a la URL
            self.driver.get(self.url)
            await asyncio.sleep(3)
            
            # Esperar a que cargue la tabla
            self.wait_for_selector(self.selectors.get('tabla_proyectos'))
            
            current_page = 1
            max_pages = self.config.get('limits', {}).get('max_pages', None)
            
            while True:
                self.logger.info(f"📄 Procesando página {current_page}")
                
                # Extraer proyectos de la página actual
                proyectos = await self._extract_projects_from_page()
                self.logger.info(f"✅ Extraídos {len(proyectos)} proyectos")
                
                # Verificar límite
                if max_pages and current_page >= max_pages:
                    break
                
                # Ir a siguiente página
                has_next = await self.next_page(current_page)
                if not has_next:
                    break
                
                current_page += 1
                await asyncio.sleep(2)
            
            self.logger.info(f"✨ Total extraídos: {len(self.results)}")
            
        except Exception as e:
            self.logger.error(f"❌ Error: {str(e)}", exc_info=True)
        finally:
            self.teardown_driver()
        
        return self.get_results()
    
    async def _extract_projects_from_page(self) -> List[Dict[str, Any]]:
        """Extrae proyectos de la página actual"""
        proyectos = []
        
        # Obtener todas las filas
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            self.selectors.get('tabla_proyectos')
        )
        
        for idx, row in enumerate(rows, 1):
            try:
                # Extraer datos de la fila
                proyecto = self._extract_row_data(row)
                
                # Agregar resultado
                self.add_result(proyecto)
                proyectos.append(proyecto)
                
            except Exception as e:
                self.logger.error(f"Error en fila {idx}: {e}")
                continue
        
        return proyectos
    
    def _extract_row_data(self, row) -> Dict[str, Any]:
        """Extrae datos de una fila"""
        data = {}
        
        # Opción 1: Extraer por índice de columna
        cells = row.find_elements(By.TAG_NAME, 'td')
        if len(cells) >= 3:
            data['numero'] = cells[0].text.strip()
            data['titulo'] = cells[1].text.strip()
            data['fecha'] = cells[2].text.strip()
        
        # Opción 2: Usar TableExtractor helper
        # column_mapping = {0: 'numero', 1: 'titulo', 2: 'fecha'}
        # data = TableExtractor.extract_row_dict(row, column_mapping)
        
        # Extraer enlace
        link_url, link_type = LinkExtractor.extract_link(row, 'a')
        data['url_detalle'] = link_url
        
        return data
```

### Paso 3: Registrar el Scraper

Edita `app/utils/scraper_factory.py`:

```python
def register_scrapers():
    """Registra automáticamente todos los scrapers disponibles"""
    from ..dominios.camara.colombia import CamaraColumbiaScraper
    from ..dominios.congreso.nuevo_pais import CongresoNuevoPaisScraper  # ✅ Nuevo
    
    scraper_factory.register('colombia_camara', CamaraColumbiaScraper)
    scraper_factory.register('nuevopais_congreso', CongresoNuevoPaisScraper)  # ✅ Nuevo
```

### Paso 4: ¡Listo para Usar!

```bash
# Probar tu scraper
curl -X POST "http://localhost:8000/api/scrape/nuevopais/congreso?max_pages=1"
```

---

## Probar tu Scraper

### 1. Test Rápido (1 página)

```bash
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?max_pages=1"
```

### 2. Ver Configuración

```bash
curl http://localhost:8000/api/config/colombia
```

### 3. Listar Scrapers Disponibles

```bash
curl http://localhost:8000/api/scrapers/available
```

### 4. Test con Filtros

```bash
# Por legislatura
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?legislatura=2024-2025&max_pages=1"

# Por fecha
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?fecha_inicio=01-11-2024&max_pages=1"
```

### 5. Documentación Interactiva

Abre en el navegador: `http://localhost:8000/docs`

---

## Helpers Disponibles

### 📅 DateParser - Parsing de Fechas

```python
from app.scrapers.helpers import DateParser

# Parsear fecha (prueba múltiples formatos automáticamente)
fecha = DateParser.parse_date("25/11/2024")
# Soporta: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.

# Extraer fecha de un texto
texto = "Fecha de Radicación: 25/11/2024"
fecha_str = DateParser.extract_date_from_text(texto)
# Retorna: "25/11/2024"
```

### 📝 TextExtractor - Extracción de Texto

```python
from app.scrapers.helpers import TextExtractor
from selenium.webdriver.common.by import By

# Extraer texto de un elemento hijo
texto = TextExtractor.extract_text(
    element=row,
    selector="td.titulo",
    by=By.CSS_SELECTOR
)

# Extraer texto N líneas después de una keyword
page_text = driver.find_element(By.TAG_NAME, 'body').text
resumen = TextExtractor.extract_text_from_lines(
    text=page_text,
    keyword="Resumen del Proyecto",
    lines_after=1
)
```

### 🔗 LinkExtractor - Extracción de Enlaces

```python
from app.scrapers.helpers import LinkExtractor

# Extraer enlace y clasificarlo automáticamente
url, tipo = LinkExtractor.extract_link(
    element=row,
    selector="a.documento",
    by=By.CSS_SELECTOR
)

# tipo puede ser: 'pdf', 'web', 'doc', 'unknown'
if tipo == 'pdf':
    print(f"Encontrado PDF: {url}")
```

### 📊 TableExtractor - Extracción de Tablas

```python
from app.scrapers.helpers import TableExtractor

# Opción 1: Extraer como lista
celdas = TableExtractor.extract_row_cells(row)
# Retorna: ['001', 'Ley de Transparencia', '25/11/2024', ...]

# Opción 2: Extraer como diccionario con mapeo
column_mapping = {
    0: 'numero',
    1: 'titulo',
    2: 'fecha',
    3: 'estado'
}
data = TableExtractor.extract_row_dict(row, column_mapping)
# Retorna: {'numero': '001', 'titulo': 'Ley...', ...}
```

---

## Debugging

### Ver Logs del Scraper

Los logs se imprimen en la consola donde corre el servidor:

```
2024-11-27 20:30:15 - [INFO] - CamaraColumbiaScraper - 🚀 Iniciando scraping
2024-11-27 20:30:18 - [INFO] - CamaraColumbiaScraper - ✅ ChromeDriver iniciado
2024-11-27 20:30:20 - [INFO] - CamaraColumbiaScraper - 📄 Procesando página 1
```

### Cambiar Nivel de Logging

En tu config JSON:

```json
{
  "log_level": "DEBUG"  // Opciones: DEBUG, INFO, WARNING, ERROR
}
```

### Ver ChromeDriver (No Headless)

Para debugging visual, temporalmente quita el modo headless en `app/scrapers/selenium.py`:

```python
def setup_driver(self):
    chrome_options = Options()
    # chrome_options.add_argument('--headless=new')  # ⬅️ Comentar esta línea
    chrome_options.add_argument('--no-sandbox')
    # ...
```

### Test Unitario Rápido

```python
# test_scraper.py
import asyncio
from app.dominios.camara.colombia import CamaraColumbiaScraper
from app.utils.config_loader import config_loader

async def test():
    config = config_loader.load('colombia')
    config['limits']['max_pages'] = 1
    
    scraper = CamaraColumbiaScraper(config)
    results = await scraper.scrape()
    
    print(f"✅ Extraídos {len(results)} proyectos")
    if results:
        print(results[0])

asyncio.run(test())
```

### Errores Comunes

#### 1. ChromeDriver no encontrado

```
Error: ChromeDriver not found at /path/to/chromedriver
```

**Solución**: Actualiza la ruta en tu config JSON:

```json
{
  "selenium": {
    "driver_path": "/usr/local/bin/chromedriver"  // Tu ruta correcta
  }
}
```

#### 2. Selector no encontrado

```
TimeoutException: El elemento 'table tbody tr' no apareció
```

**Solución**:
- Abre la página en el navegador
- Inspecciona el elemento (F12)
- Verifica el selector CSS correcto
- Actualiza en tu config JSON

#### 3. Scraper no registrado

```
ValueError: Scraper 'nuevopais_congreso' no encontrado
```

**Solución**: Verifica que registraste el scraper en `app/utils/scraper_factory.py`

---

## Estructura de un Scraper Mínimo

```python
from typing import Dict, Any
from ...scrapers.selenium import SeleniumScraper

class MiScraper(SeleniumScraper):
    async def scrape(self):
        try:
            # 1. Setup
            self.setup_driver()
            self.driver.get(self.url)
            
            # 2. Extraer datos
            # ... tu lógica aquí ...
            
            # 3. Guardar resultados
            self.add_result({'campo': 'valor'})
            
        finally:
            # 4. Cleanup
            self.teardown_driver()
        
        return self.get_results()
```

---

## Próximos Pasos

1. ✅ Crea tu configuración JSON
2. ✅ Crea tu clase de scraper
3. ✅ Regístrala en el factory
4. ✅ Prueba con `max_pages=1`
5. ✅ Ajusta selectores si es necesario
6. ✅ Ejecuta scraping completo

---

**¿Dudas?** Revisa el scraper de Colombia en `app/dominios/camara/colombia.py` como referencia completa.
