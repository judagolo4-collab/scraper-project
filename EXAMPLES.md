# 📚 Ejemplos de Uso

## 1. Uso Básico - Scraping Completo

### Con cURL

```bash
# Scraping de todos los proyectos de Colombia
curl -X POST "http://localhost:8000/api/scrape/colombia" \
  -H "Content-Type: application/json" | jq '.'
```

### Con Python (requests)

```python
import requests

# Ejecutar scraping
response = requests.post("http://localhost:8000/api/scrape/colombia")
data = response.json()

print(f"Total proyectos: {data['total_proyectos']}")
print(f"Mensaje: {data['message']}")

# Acceder a los proyectos
for proyecto in data['proyectos']:
    print(f"- {proyecto['titulo']}")
    print(f"  PDF: {proyecto['url_pdf']}")
```

### Con JavaScript (fetch)

```javascript
// Ejecutar scraping
fetch('http://localhost:8000/api/scrape/colombia', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  console.log(`Total proyectos: ${data.total_proyectos}`);
  
  data.proyectos.forEach(proyecto => {
    console.log(`${proyecto.titulo} - ${proyecto.estado}`);
  });
});
```

## 2. Filtrado por Legislatura

### Con cURL

```bash
# Solo proyectos de la legislatura 2024-2025
curl -X POST "http://localhost:8000/api/scrape/colombia?legislatura=2024-2025" \
  -H "Content-Type: application/json"
```

### Con Python

```python
import requests

# Filtrar por legislatura
params = {'legislatura': '2024-2025'}
response = requests.post(
    "http://localhost:8000/api/scrape/colombia",
    params=params
)

data = response.json()
print(f"Proyectos de 2024-2025: {data['total_proyectos']}")
```

## 3. Procesamiento de Resultados

### Guardar en CSV

```python
import requests
import csv

# Ejecutar scraping
response = requests.post("http://localhost:8000/api/scrape/colombia")
data = response.json()

# Guardar en CSV
with open('proyectos_colombia.csv', 'w', newline='', encoding='utf-8') as f:
    if data['proyectos']:
        writer = csv.DictWriter(f, fieldnames=data['proyectos'][0].keys())
        writer.writeheader()
        writer.writerows(data['proyectos'])

print("✅ Datos guardados en proyectos_colombia.csv")
```

### Guardar en JSON

```python
import requests
import json

# Ejecutar scraping
response = requests.post("http://localhost:8000/api/scrape/colombia")
data = response.json()

# Guardar en JSON
with open('proyectos_colombia.json', 'w', encoding='utf-8') as f:
    json.dump(data['proyectos'], f, ensure_ascii=False, indent=2)

print("✅ Datos guardados en proyectos_colombia.json")
```

### Filtrar proyectos por estado

```python
import requests

response = requests.post("http://localhost:8000/api/scrape/colombia")
data = response.json()

# Filtrar solo proyectos "En trámite"
en_tramite = [
    p for p in data['proyectos'] 
    if p.get('estado') == 'En trámite'
]

print(f"Proyectos en trámite: {len(en_tramite)}")

# Agrupar por comisión
from collections import defaultdict
por_comision = defaultdict(list)

for proyecto in data['proyectos']:
    comision = proyecto.get('comision', 'Sin comisión')
    por_comision[comision].append(proyecto)

for comision, proyectos in por_comision.items():
    print(f"{comision}: {len(proyectos)} proyectos")
```

## 4. Descargar PDFs

```python
import requests
import os
from urllib.parse import urlparse

# Ejecutar scraping
response = requests.post("http://localhost:8000/api/scrape/colombia")
data = response.json()

# Crear directorio para PDFs
os.makedirs('pdfs_colombia', exist_ok=True)

# Descargar PDFs
for proyecto in data['proyectos']:
    url_pdf = proyecto.get('url_pdf')
    if url_pdf:
        try:
            # Obtener nombre del archivo
            filename = os.path.basename(urlparse(url_pdf).path)
            filepath = os.path.join('pdfs_colombia', filename)
            
            # Descargar
            pdf_response = requests.get(url_pdf, timeout=30)
            pdf_response.raise_for_status()
            
            # Guardar
            with open(filepath, 'wb') as f:
                f.write(pdf_response.content)
            
            print(f"✅ Descargado: {filename}")
        except Exception as e:
            print(f"❌ Error descargando {url_pdf}: {e}")

print("✅ Descarga de PDFs completada")
```

## 5. Uso Programático del Scraper

### Importar directamente el scraper

```python
import asyncio
import yaml
from app.dominios.camara.colombia import CamaraColumbiaScraper

# Cargar configuración
with open('config/colombia.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Crear scraper
scraper = CamaraColumbiaScraper(config, legislatura_filter="2024-2025")

# Ejecutar scraping
async def main():
    resultados = await scraper.scrape()
    print(f"Total: {len(resultados)} proyectos")
    return resultados

# Ejecutar
resultados = asyncio.run(main())
```

### Personalizar configuración

```python
import asyncio
from app.dominios.camara.colombia import CamaraColumbiaScraper

# Configuración personalizada
config = {
    "pais": "Colombia",
    "url": "https://www.camara.gov.co/secretaria/proyectos-de-ley#menu",
    "selenium": {
        "wait_time": 15,  # Más tiempo de espera
        "driver_path": "/usr/local/bin/chromedriver"
    },
    "selectors": {
        "tabla_proyectos": "table tbody tr",
        "paginacion_siguiente": "button.pagina-btn[data-pagina='next']"
    },
    "pagination": {
        "next_button": "button.pagina-btn[data-pagina='next']",
        "click_delay": 3  # Más delay entre páginas
    },
    "log_level": "DEBUG"
}

scraper = CamaraColumbiaScraper(config)
resultados = asyncio.run(scraper.scrape())
```

## 6. Integración con Pandas

```python
import requests
import pandas as pd

# Ejecutar scraping
response = requests.post("http://localhost:8000/api/scrape/colombia")
data = response.json()

# Crear DataFrame
df = pd.DataFrame(data['proyectos'])

# Análisis básico
print(f"Total proyectos: {len(df)}")
print(f"\nProyectos por estado:")
print(df['estado'].value_counts())

print(f"\nProyectos por comisión:")
print(df['comision'].value_counts())

print(f"\nProyectos por legislatura:")
print(df['legislatura'].value_counts())

# Filtrar y exportar
proyectos_2024 = df[df['legislatura'] == '2024-2025']
proyectos_2024.to_excel('proyectos_2024.xlsx', index=False)

print(f"\n✅ Exportados {len(proyectos_2024)} proyectos a Excel")
```

## 7. Monitoreo y Logging

### Ver logs en tiempo real

```bash
# Con Docker
docker logs scraper-api -f

# Local
# Los logs aparecen en la consola donde ejecutaste uvicorn
```

### Configurar nivel de logging

En `config/colombia.yaml`:
```yaml
log_level: "DEBUG"  # Para ver todos los detalles
```

### Capturar logs en Python

```python
import logging
import asyncio
from app.dominios.camara.colombia import CamaraColumbiaScraper

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

# Ejecutar scraping (los logs se guardarán en scraping.log)
config = {...}
scraper = CamaraColumbiaScraper(config)
resultados = asyncio.run(scraper.scrape())
```

## 8. Manejo de Errores

```python
import requests
from requests.exceptions import RequestException, Timeout

try:
    response = requests.post(
        "http://localhost:8000/api/scrape/colombia",
        timeout=3600  # 1 hora de timeout
    )
    response.raise_for_status()
    
    data = response.json()
    
    if data['success']:
        print(f"✅ Scraping exitoso: {data['total_proyectos']} proyectos")
    else:
        print(f"❌ Error: {data['message']}")
        
except Timeout:
    print("❌ Timeout: El scraping tomó demasiado tiempo")
except RequestException as e:
    print(f"❌ Error de conexión: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
```

## 9. Scraping Programado (Cron)

### Script de scraping diario

```python
#!/usr/bin/env python3
# scrape_daily.py

import requests
import json
from datetime import datetime
import os

def scrape_and_save():
    """Ejecuta scraping y guarda resultados con timestamp"""
    
    print(f"[{datetime.now()}] Iniciando scraping...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/scrape/colombia",
            timeout=7200  # 2 horas
        )
        response.raise_for_status()
        data = response.json()
        
        # Guardar con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraping_colombia_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Scraping completado: {data['total_proyectos']} proyectos")
        print(f"✅ Guardado en: {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Aquí podrías enviar una notificación por email

if __name__ == "__main__":
    scrape_and_save()
```

### Configurar cron (Linux/Mac)

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar diariamente a las 2 AM
0 2 * * * /usr/bin/python3 /path/to/scrape_daily.py >> /path/to/scraping.log 2>&1
```

## 10. Testing

### Ejecutar tests

```bash
# Todos los tests
make test

# Con cobertura
make test-cov

# Solo tests de Colombia
pytest tests/unit/colombia/ -v

# Test específico
pytest tests/unit/colombia/test_colombia.py::test_scraper_initialization -v
```

### Escribir un nuevo test

```python
# tests/unit/colombia/test_custom.py

import pytest
from app.dominios.camara.colombia import CamaraColumbiaScraper

def test_filtro_legislatura():
    """Test de filtrado por legislatura"""
    config = {
        "url": "https://www.camara.gov.co/secretaria/proyectos-de-ley#menu",
        "selenium": {"wait_time": 10},
        "selectors": {},
        "log_level": "INFO"
    }
    
    scraper = CamaraColumbiaScraper(config, legislatura_filter="2024-2025")
    assert scraper.legislatura_filter == "2024-2025"
```

---

## 💡 Tips y Mejores Prácticas

1. **Timeout adecuado**: El scraping completo puede tomar horas, ajusta el timeout
2. **Manejo de errores**: Siempre captura excepciones para evitar pérdida de datos
3. **Logging**: Usa nivel DEBUG durante desarrollo, INFO en producción
4. **Filtros**: Usa filtro de legislatura para pruebas rápidas
5. **Guardado incremental**: Considera guardar resultados cada N páginas
6. **Rate limiting**: Respeta el servidor, usa delays apropiados
7. **Backup**: Guarda resultados con timestamps para tener histórico

## 🔗 Referencias

- Documentación FastAPI: https://fastapi.tiangolo.com/
- Selenium Python: https://selenium-python.readthedocs.io/
- Pytest: https://docs.pytest.org/
