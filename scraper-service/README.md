# ⚡ Scraper Service API

Microservicio especializado en la extracción de datos legislativos. Expone una API REST unificada para invocar scrapers de diferentes países, abstrayendo la complejidad técnica de cada sitio web.

---

## ✨ Características Principales

*   **Arquitectura Modular**: Diseño basado en patrones Factory y Strategy. Agregar un nuevo país es tan simple como crear un archivo de configuración y una clase heredada.
*   **Múltiples Motores de Scraping**:
    *   **AJAX Scraper**: Para sitios que cargan datos vía APIs internas (ej. Colombia). Extremadamente rápido.
    *   **HTML Scraper (HTTPx)**: Para sitios estáticos (ej. Perú). Ligero y veloz.
    *   **Selenium Scraper**: Para sitios complejos con alto uso de JavaScript dinámico.
*   **Integración con Gemini AI**: Clasificación automática de proyectos de ley en sectores económicos (Salud, Economía, Educación, etc.) usando IA.
*   **API RESTful**: Documentación automática con Swagger UI.

---

## 🔌 Endpoints API

### 1. Scraping Genérico
Ejecuta el scraper para un país específico.

`POST /api/scrape/{country}`

**Parámetros:**
*   `country`: `colombia` | `peru`
*   `tipo_scraper`: `ajax` | `selenium` (Depende del soporte del país)
*   `max_pages`: Límite de páginas a procesar (1-100)
*   `classify`: `true` | `false` (Activar clasificación con IA)

**Filtros (Colombia):**
*   `legislatura`, `tipo`, `estado`, `origen`, `comision`

**Ejemplo de Respuesta:**
```json
{
  "success": true,
  "total_proyectos": 50,
  "proyectos": [
    {
      "numero": "123/2024",
      "titulo": "PROYECTO DE LEY...",
      "estado": "Aprobado",
      "sector_economico": "Salud",
      "url_detalle": "https://..."
    }
  ]
}
```

### 2. Utilidades Gemini
`GET /api/gemini/sectores`
Retorna la lista de sectores económicos utilizados para la clasificación.

---

## 🔧 Desarrollo Local

### Estructura
```
scraper-service/
├── app/
│   ├── dominios/           # Lógica de negocio por país
│   │   ├── camara/         # Colombia
│   │   └── congreso/       # Perú
│   ├── scrapers/           # Motores base
│   │   ├── base.py         # Clase abstracta
│   │   ├── ajax_scraper.py # Motor AJAX
│   │   ├── html_scraper.py # Motor HTTPx
│   │   └── selenium.py     # Motor Selenium
│   ├── services/           # Servicios externos (Gemini)
│   └── utils/              # Factory y loaders
```

### Cómo agregar un nuevo país

1.  **Configuración**: Crea un archivo `{pais}.json` en la carpeta `config/` con los selectores CSS/XPath y URLs base.
2.  **Implementación**: Crea una clase en `app/dominios/congreso/{pais}.py` que herede del scraper adecuado (`HTMLScraper` o `SeleniumScraper`).
3.  **Registro**: Registra la nueva clase en `app/utils/scraper_factory.py`.

¡Listo! La API lo reconocerá automáticamente.

---

## 🧪 Tests

El servicio incluye tests unitarios y de integración.

```bash
# Ejecutar tests dentro del contenedor
docker exec -it scraper-api pytest
```

