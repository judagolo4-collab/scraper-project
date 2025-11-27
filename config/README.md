# 🔧 Configuración de Scrapers

Este directorio contiene las configuraciones en formato JSON para cada scraper de país/institución.

## 📋 Formato del JSON

Cada archivo de configuración debe seguir esta estructura:

```json
{
  "url": "string",              // URL base del sitio a scrapear
  "institution": "string",       // Tipo de institución (camara, senado, congreso)
  "selectors": {                // Selectores CSS/XPath para extraer datos
    "table": "string",          // Selector de la tabla principal
    "rows": "string",           // Selector de las filas
    "detail_link": "string",    // Selector del link de detalle
    "fields": {                 // Campos a extraer
      "field_name": "string"    // Selector para cada campo
    }
  },
  "pagination": {               // Configuración de paginación
    "next_button": "string",    // Selector del botón "siguiente"
    "wait_time": number,        // Tiempo de espera entre páginas (segundos)
    "max_retries": number       // Reintentos en caso de error
  },
  "limits": {                   // Límites opcionales
    "max_pages": number,        // Máximo de páginas a procesar
    "max_projects": number      // Máximo de proyectos a extraer
  },
  "filters": {                  // Filtros opcionales
    "legislatura": "string",    // Filtro por legislatura
    "year": number              // Filtro por año
  }
}
```

## 📝 Ejemplo Completo: Colombia - Cámara de Representantes

Ver: `colombia.json`

```json
{
  "url": "https://www.camara.gov.co/secretaria/proyectos-de-ley#menu",
  "institution": "camara",
  "selectors": {
    "table": "table.listado-pley",
    "rows": "tbody tr",
    "detail_link": "td:nth-child(2) a",
    "fields": {
      "numero_camara": "td:nth-child(1)",
      "titulo": "td:nth-child(2) a",
      "tipo": "td:nth-child(3)",
      "autores": "td:nth-child(4)",
      "estado": "td:nth-child(5)",
      "origen": "td:nth-child(6)",
      "comision": "td:nth-child(7)",
      "legislatura": "td:nth-child(8)"
    }
  },
  "detail_selectors": {
    "fecha_radicacion": ".date-display-single",
    "resumen": ".field-name-body",
    "pdf_link": "a[href*='.pdf']",
    "gaceta_link": "a[href*='gaceta']"
  },
  "pagination": {
    "next_button": "a.next",
    "wait_time": 2,
    "max_retries": 3
  }
}
```

## 🎯 Campos Requeridos vs Opcionales

### ✅ Requeridos
- `url`: URL del sitio a scrapear
- `institution`: Tipo de institución
- `selectors.table`: Selector de la tabla
- `selectors.rows`: Selector de las filas
- `selectors.fields`: Al menos un campo a extraer

### 📌 Opcionales
- `selectors.detail_link`: Si hay página de detalle
- `detail_selectors`: Selectores para la página de detalle
- `pagination`: Si hay múltiples páginas
- `limits`: Para limitar el scraping
- `filters`: Para filtrar resultados

## 🔍 Tipos de Selectores Soportados

### CSS Selectors (recomendado)
```json
{
  "fields": {
    "titulo": "td:nth-child(2) a",
    "estado": ".status-cell",
    "fecha": "span.date"
  }
}
```

### XPath (cuando CSS no es suficiente)
```json
{
  "fields": {
    "titulo": "//td[2]/a",
    "autor": "//div[@class='author']/text()"
  }
}
```

## 🚀 Crear Nueva Configuración

Para agregar un nuevo país/institución:

1. **Crear el archivo JSON:**
   ```bash
   touch config/nuevo_pais.json
   ```

2. **Copiar la estructura base:**
   - Usa `colombia.json` como referencia
   - Ajusta los selectores según el sitio web

3. **Probar la configuración:**
   ```python
   # Test rápido
   python tests/integration/test_scraper.py
   ```

4. **Registrar el scraper:**
   ```python
   # En app/main.py o startup
   from app.utils.scraper_factory import scraper_factory
   from app.dominios.camara.nuevo_pais import NuevoPaisScraper
   
   scraper_factory.register("nuevo_pais_camara", NuevoPaisScraper)
   ```

## 📦 Nomenclatura de Archivos

Seguir el patrón:
```
{pais}.json          # Para configuración general
{pais}_{institucion}.json  # Si hay múltiples instituciones
```

Ejemplos:
- `colombia.json` → Colombia - Cámara (por defecto)
- `colombia_senado.json` → Colombia - Senado
- `peru.json` → Perú - Congreso
- `mexico_diputados.json` → México - Cámara de Diputados

## 🔄 Versionado

Si necesitas mantener múltiples versiones:
```
colombia.json           # Versión actual
colombia.v1.json       # Versión anterior (respaldo)
```

## 🛠️ Validación

El sistema validará automáticamente:
- ✅ Campos requeridos presentes
- ✅ Formato JSON válido
- ✅ URLs accesibles
- ⚠️ Selectores (solo en runtime)

## 💡 Tips

1. **Usar nth-child con cuidado**: Puede cambiar si la estructura HTML cambia
2. **Preferir clases/IDs estables**: Más resistente a cambios
3. **Incluir wait_time adecuado**: Evita sobrecargar el servidor
4. **Documentar selectores especiales**: Si usas lógica compleja
5. **Probar con max_pages=1**: Antes de scrapear todo el sitio

## 🐛 Debug

Si los selectores no funcionan:

```python
# Test manual de selectores
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("URL_DEL_SITIO")

# Probar selector
elementos = driver.find_elements(By.CSS_SELECTOR, "tu_selector")
print(f"Encontrados: {len(elementos)}")
```

## 📚 Referencias

- [CSS Selectors](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors)
- [XPath Tutorial](https://www.w3schools.com/xml/xpath_intro.asp)
- [Selenium Documentation](https://www.selenium.dev/documentation/)

