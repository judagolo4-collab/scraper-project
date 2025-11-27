# 📚 EXAMPLES - Ejemplos de Uso

Este archivo contiene ejemplos prácticos de cómo usar el sistema de scraping.

---

## 📋 Tabla de Contenidos

- [Ejecutar Scraping Simple](#ejecutar-scraping-simple)
- [Scraping con Filtros](#scraping-con-filtros)
- [Usar Helpers en tu Scraper](#usar-helpers-en-tu-scraper)
- [Crear Scraper Personalizado](#crear-scraper-personalizado)
- [Ejemplos de Configuración](#ejemplos-de-configuración)

---

## Ejecutar Scraping Simple

### Usando cURL

```bash
# Scraping completo (todas las páginas)
curl -X POST "http://localhost:8000/api/scrape/colombia/camara"

# Solo 1 página (útil para pruebas)
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?max_pages=1"

# 5 páginas
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?max_pages=5"
```

### Usando Python

```python
import requests

# Scraping simple
response = requests.post(
    "http://localhost:8000/api/scrape/colombia/camara",
    params={"max_pages": 1}
)

data = response.json()
print(f"Total proyectos: {data['total_proyectos']}")
print(f"Primer proyecto: {data['proyectos'][0]['titulo']}")
```

### Usando JavaScript (fetch)

```javascript
// Scraping simple
fetch('http://localhost:8000/api/scrape/colombia/camara?max_pages=1', {
  method: 'POST'
})
  .then(res => res.json())
  .then(data => {
    console.log(`Total: ${data.total_proyectos}`);
    console.log('Proyectos:', data.proyectos);
  });
```

---

## Scraping con Filtros

### Por Legislatura

```bash
# Solo proyectos de legislatura 2024-2025
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?legislatura=2024-2025&max_pages=3"
```

```python
response = requests.post(
    "http://localhost:8000/api/scrape/colombia/camara",
    params={
        "legislatura": "2024-2025",
        "max_pages": 3
    }
)
```

### Por Fecha (Carga Incremental)

```bash
# Solo proyectos desde 01 de Noviembre 2024
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?fecha_inicio=01-11-2024"
```

```python
response = requests.post(
    "http://localhost:8000/api/scrape/colombia/camara",
    params={
        "fecha_inicio": "01-11-2024"  # Formato: DD-MM-YYYY
    }
)
```

**Nota**: Con `fecha_inicio`, el scraper se detendrá automáticamente al encontrar proyectos anteriores a esa fecha, ahorrando tiempo.

### Combinar Filtros

```bash
# Legislatura específica + máximo de páginas + fecha
curl -X POST "http://localhost:8000/api/scrape/colombia/camara?legislatura=2024-2025&max_pages=5&fecha_inicio=15-08-2024"
```

---

## Usar Helpers en tu Scraper

### Ejemplo 1: Parsear Fechas

```python
from app.scrapers.helpers import DateParser

# En tu método de extracción
def _extract_row_data(self, row):
    data = {}
    
    # Extraer texto de fecha (puede estar en varios formatos)
    fecha_str = row.find_element(By.CSS_SELECTOR, 'td.fecha').text
    # fecha_str podría ser: "25/11/2024", "25-11-2024", etc.
    
    # Parsear automáticamente (prueba múltiples formatos)
    fecha_obj = DateParser.parse_date(fecha_str)
    
    if fecha_obj:
        # Guardar en formato estándar
        data['fecha'] = fecha_obj.strftime('%Y-%m-%d')
    else:
        data['fecha'] = None
    
    return data
```

### Ejemplo 2: Extraer Texto Estructurado

```python
from app.scrapers.helpers import TextExtractor

async def _extract_detail_page(self, url):
    detail_data = {}
    
    # Obtener texto completo de la página
    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
    
    # Extraer resumen (1 línea después de "Resumen:")
    resumen = TextExtractor.extract_text_from_lines(
        text=page_text,
        keyword="Resumen:",
        lines_after=1
    )
    detail_data['resumen'] = resumen
    
    # Extraer autor (2 líneas después de "Autor:")
    autor = TextExtractor.extract_text_from_lines(
        text=page_text,
        keyword="Autor:",
        lines_after=2
    )
    detail_data['autor'] = autor
    
    return detail_data
```

### Ejemplo 3: Extraer y Clasificar Enlaces

```python
from app.scrapers.helpers import LinkExtractor
from selenium.webdriver.common.by import By

def _extract_row_data(self, row):
    data = {}
    
    # Extraer enlace al PDF
    pdf_url, link_type = LinkExtractor.extract_link(
        element=row,
        selector="a.documento",
        by=By.CSS_SELECTOR
    )
    
    # link_type será: 'pdf', 'web', 'doc', o 'unknown'
    if link_type == 'pdf':
        data['url_pdf'] = pdf_url
        self.logger.info(f"📄 PDF encontrado: {pdf_url}")
    elif link_type == 'web':
        data['url_web'] = pdf_url
    else:
        self.logger.warning(f"⚠️ Enlace de tipo desconocido: {pdf_url}")
    
    return data
```

### Ejemplo 4: Extraer Tabla Completa

```python
from app.scrapers.helpers import TableExtractor
from selenium.webdriver.common.by import By

async def _extract_projects_from_page(self):
    proyectos = []
    
    # Obtener todas las filas de la tabla
    rows = self.driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
    
    # Definir mapeo de columnas
    column_mapping = {
        0: 'numero',
        1: 'titulo',
        2: 'fecha',
        3: 'autor',
        4: 'estado',
        5: 'comision'
    }
    
    for row in rows:
        # Extraer datos usando el mapeo
        proyecto = TableExtractor.extract_row_dict(row, column_mapping)
        
        # Agregar metadatos adicionales
        proyecto['pais'] = self.config['pais']
        proyecto['institucion'] = self.config['institucion']
        
        self.add_result(proyecto)
        proyectos.append(proyecto)
    
    return proyectos
```

---

## Crear Scraper Personalizado

### Ejemplo Completo: Scraper para Perú

#### 1. Configuración (`config/peru.json`)

```json
{
  "pais": "Peru",
  "institucion": "Congreso",
  "url": "https://www.congreso.gob.pe/pleno/proyectos-de-ley",
  "selenium": {
    "wait_time": 10,
    "driver_path": "/usr/local/bin/chromedriver"
  },
  "selectors": {
    "tabla_proyectos": "table#proyectos tbody tr",
    "boton_siguiente": "button.pagina-siguiente",
    "link_detalle": "a.ver-detalle"
  },
  "pagination": {
    "next_button": "button.pagina-siguiente",
    "click_delay": 2
  },
  "limits": {
    "max_pages": null,
    "request_delay": 1
  },
  "log_level": "INFO"
}
```

#### 2. Scraper (`app/dominios/congreso/peru.py`)

```python
# peru.py - Scraper para Congreso de Perú

from typing import List, Dict, Any
import asyncio
from selenium.webdriver.common.by import By
from ...scrapers.selenium import SeleniumScraper
from ...scrapers.helpers import (
    DateParser,
    TextExtractor,
    LinkExtractor,
    TableExtractor
)


class CongresoPeruScraper(SeleniumScraper):
    """
    Scraper para el Congreso de Perú.
    Extrae proyectos de ley desde el portal legislativo.
    """
    
    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(config)
        self.selectors = config.get('selectors', {})
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Método principal de scraping"""
        try:
            self.setup_driver()
            self.logger.info("🚀 Iniciando scraping del Congreso de Perú")
            
            # Navegar a la URL
            self.driver.get(self.url)
            await asyncio.sleep(3)
            
            # Esperar tabla de proyectos
            self.wait_for_selector(self.selectors['tabla_proyectos'])
            
            current_page = 1
            max_pages = self.config.get('limits', {}).get('max_pages', None)
            
            while True:
                self.logger.info(f"📄 Procesando página {current_page}")
                
                # Extraer proyectos
                proyectos = await self._extract_projects_from_page()
                self.logger.info(f"✅ Extraídos {len(proyectos)} proyectos")
                
                # Verificar límite
                if max_pages and current_page >= max_pages:
                    break
                
                # Siguiente página
                has_next = await self.next_page(current_page)
                if not has_next:
                    break
                
                current_page += 1
                await asyncio.sleep(2)
            
            self.logger.info(f"✨ Total: {len(self.results)} proyectos")
            
        except Exception as e:
            self.logger.error(f"❌ Error: {str(e)}", exc_info=True)
        finally:
            self.teardown_driver()
        
        return self.get_results()
    
    async def _extract_projects_from_page(self) -> List[Dict[str, Any]]:
        """Extrae proyectos de la página actual"""
        proyectos = []
        
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            self.selectors['tabla_proyectos']
        )
        
        # Mapeo de columnas específico de Perú
        column_mapping = {
            0: 'numero_expediente',
            1: 'titulo',
            2: 'fecha_presentacion',
            3: 'proponente',
            4: 'estado_actual'
        }
        
        for idx, row in enumerate(rows, 1):
            try:
                # Extraer datos usando helper
                proyecto = TableExtractor.extract_row_dict(row, column_mapping)
                
                # Parsear fecha
                if proyecto.get('fecha_presentacion'):
                    fecha_obj = DateParser.parse_date(proyecto['fecha_presentacion'])
                    if fecha_obj:
                        proyecto['fecha_presentacion'] = fecha_obj.strftime('%Y-%m-%d')
                
                # Extraer enlace de detalle
                link_url, _ = LinkExtractor.extract_link(
                    row,
                    self.selectors['link_detalle']
                )
                proyecto['url_detalle'] = link_url
                
                # Agregar metadatos
                proyecto['pais'] = 'Peru'
                proyecto['institucion'] = 'Congreso'
                
                # Guardar
                self.add_result(proyecto)
                proyectos.append(proyecto)
                
            except Exception as e:
                self.logger.error(f"Error en fila {idx}: {e}")
                continue
        
        return proyectos
```

#### 3. Registro (`app/utils/scraper_factory.py`)

```python
def register_scrapers():
    from ..dominios.camara.colombia import CamaraColumbiaScraper
    from ..dominios.congreso.peru import CongresoPeruScraper  # ✅ Importar
    
    scraper_factory.register('colombia_camara', CamaraColumbiaScraper)
    scraper_factory.register('peru_congreso', CongresoPeruScraper)  # ✅ Registrar
```

#### 4. Uso

```bash
# Probar scraper de Perú
curl -X POST "http://localhost:8000/api/scrape/peru/congreso?max_pages=1"
```

---

## Ejemplos de Configuración

### Paginación por URL

```json
{
  "pagination": {
    "param_name": "page",
    "click_delay": 2
  }
}
```

El scraper navegará: `url?page=1`, `url?page=2`, etc.

### Paginación por Botón

```json
{
  "pagination": {
    "next_button": "button.next-page",
    "click_delay": 2
  }
}
```

El scraper hará click en el botón de siguiente página.

### Sin Paginación (Una Sola Página)

```json
{
  "pagination": null
}
```

### Selectores Mixtos (CSS y XPath)

```json
{
  "selectors": {
    "tabla_proyectos": "table tbody tr",
    "titulo_xpath": "//h1[@class='titulo-proyecto']",
    "pdf_link": "div.documentos a[href$='.pdf']",
    "autor_xpath": "//span[contains(text(), 'Autor')]/following-sibling::span[1]"
  }
}
```

### Límites Personalizados

```json
{
  "limits": {
    "max_pages": 10,
    "max_projects_per_page": 50,
    "request_delay": 2
  }
}
```

---

## Script de Prueba Completo

```python
#!/usr/bin/env python3
"""
Script para probar scrapers localmente
"""
import asyncio
import sys
from app.utils.config_loader import config_loader
from app.utils.scraper_factory import scraper_factory


async def test_scraper(country: str, institution: str, max_pages: int = 1):
    """Prueba un scraper localmente"""
    print(f"🧪 Probando scraper: {country} - {institution}")
    
    try:
        # Cargar configuración
        config = config_loader.load(country)
        config['limits']['max_pages'] = max_pages
        
        # Crear scraper
        scraper = scraper_factory.create_by_country_institution(
            country=country,
            institution=institution,
            config=config
        )
        
        # Ejecutar
        results = await scraper.scrape()
        
        # Mostrar resultados
        print(f"\n✅ Extraídos {len(results)} proyectos")
        if results:
            print("\n📄 Primer proyecto:")
            for key, value in results[0].items():
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python test_scraper.py <country> <institution> [max_pages]")
        print("Ejemplo: python test_scraper.py colombia camara 1")
        sys.exit(1)
    
    country = sys.argv[1]
    institution = sys.argv[2]
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    asyncio.run(test_scraper(country, institution, max_pages))
```

**Uso:**

```bash
# Probar Colombia
python test_scraper.py colombia camara 1

# Probar Perú (si lo implementaste)
python test_scraper.py peru congreso 2
```

---

## Tips y Trucos

### 1. Debugging con Logs Detallados

```json
{
  "log_level": "DEBUG"
}
```

### 2. Ver el Navegador (No Headless)

En `app/scrapers/selenium.py`, comenta temporalmente:

```python
# chrome_options.add_argument('--headless=new')
```

### 3. Pausar entre Requests

```json
{
  "limits": {
    "request_delay": 3  // Esperar 3 segundos entre páginas
  }
}
```

### 4. Selectores Robustos

Usa selectores específicos que no cambien frecuentemente:

```json
{
  "selectors": {
    "tabla_proyectos": "table#tabla-principal tbody tr",  // ✅ Con ID
    "titulo": "td[data-field='titulo']"  // ✅ Con atributo data
  }
}
```

---

**¿Más ejemplos?** Revisa la implementación completa de Colombia en:
- `config/colombia.json`
- `app/dominios/camara/colombia.py`
