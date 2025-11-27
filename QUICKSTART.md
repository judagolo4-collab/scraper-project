# 🚀 Guía de Inicio Rápido

Esta guía te ayudará a poner en marcha el proyecto de scraping en pocos minutos.

## 📋 Prerrequisitos

### Opción 1: Ejecución Local

- Python 3.11 o superior
- Google Chrome instalado
- ChromeDriver compatible con tu versión de Chrome

### Opción 2: Con Docker (Recomendado)

- Docker Desktop instalado
- Docker Compose

## 🛠️ Instalación

### Opción 1: Instalación Local

```bash
# 1. Clonar o navegar al directorio del proyecto
cd scraper

# 2. Crear y activar entorno virtual
cd scraper-service
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Volver al directorio raíz
cd ..
```

### Opción 2: Con Docker

```bash
# 1. Navegar al directorio del proyecto
cd scraper

# 2. Copiar el template de variables de entorno
cp docker/.env.template docker/.env

# 3. Levantar los servicios
make docker-up
```

## ▶️ Ejecución

### Opción 1: Ejecución Local

```bash
# Desde el directorio raíz del proyecto
make run

# O manualmente:
cd scraper-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 2: Con Docker

```bash
# Los servicios ya están corriendo después de make docker-up
# Puedes ver los logs con:
make docker-logs
```

## 🧪 Probar el Scraper

### 1. Verificar que la API está funcionando

Abre tu navegador en: http://localhost:8000

Deberías ver:
```json
{
  "message": "API de Scraping de Proyectos de Ley",
  "version": "0.1.0",
  "docs": "/docs",
  "status": "online"
}
```

### 2. Ver la documentación interactiva

Abre: http://localhost:8000/docs

Aquí encontrarás todos los endpoints disponibles con la opción de probarlos directamente.

### 3. Ejecutar el scraping de Colombia

#### Opción A: Desde la interfaz de Swagger

1. Ve a http://localhost:8000/docs
2. Busca el endpoint `POST /api/scrape/colombia`
3. Click en "Try it out"
4. (Opcional) Añade un filtro de legislatura, por ejemplo: `2024-2025`
5. Click en "Execute"

#### Opción B: Con cURL

```bash
# Scraping completo (todas las legislaturas)
curl -X POST "http://localhost:8000/api/scrape/colombia" \
  -H "Content-Type: application/json"

# Con filtro de legislatura
curl -X POST "http://localhost:8000/api/scrape/colombia?legislatura=2024-2025" \
  -H "Content-Type: application/json"
```

#### Opción C: Con el Makefile

```bash
make scrape-colombia
```

### 4. Interpretar los resultados

La respuesta será un JSON con esta estructura:

```json
{
  "success": true,
  "message": "Scraping completado exitosamente. 150 proyectos extraídos.",
  "total_proyectos": 150,
  "proyectos": [
    {
      "numero_camara": "472",
      "numero_senado": "",
      "titulo": "LEY CATASTRO MULTIPROPÓSITO",
      "tipo": "Ordinaria",
      "autores": "Gobierno Nacional",
      "estado": "En trámite",
      "origen": "Cámara",
      "comision": "Tercera",
      "legislatura": "2024-2025",
      "fecha_radicacion": "2025-11-20",
      "resumen": "Por medio de la cual se establece...",
      "url_detalle": "https://www.camara.gov.co/ley-catastro-multiproposito/",
      "url_pdf": "https://www.camara.gov.co/wp-content/uploads/.../P.L.472-2025SC-LEY-CATASTRO-MULTIPROPOSITO.pdf",
      "url_gaceta": "https://..."
    }
    // ... más proyectos
  ]
}
```

## ⚙️ Configuración

### Modificar selectores o parámetros

Edita el archivo `config/colombia.yaml`:

```yaml
# Cambiar tiempo de espera
selenium:
  wait_time: 15  # Aumentar si la página es lenta

# Modificar selectores CSS
selectors:
  tabla_proyectos: "table tbody tr"
  paginacion_siguiente: "button.pagina-btn[data-pagina='next']"

# Ajustar delays
pagination:
  click_delay: 3  # Segundos de espera entre páginas
```

### Cambiar nivel de logging

En `config/colombia.yaml`:

```yaml
log_level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

## 🐛 Solución de Problemas

### Error: "ChromeDriver not found"

**Solución Local:**
```bash
# macOS
brew install chromedriver

# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Verificar instalación
which chromedriver
```

Luego actualiza la ruta en `config/colombia.yaml`:
```yaml
selenium:
  driver_path: "/ruta/a/chromedriver"  # Usar la ruta del comando 'which'
```

**Solución Docker:**
El Dockerfile ya incluye ChromeDriver, no requiere configuración adicional.

### Error: "Timeout esperando el selector"

Esto puede ocurrir si:
- La página tarda mucho en cargar
- Los selectores CSS han cambiado

**Solución:**
1. Aumenta el `wait_time` en `config/colombia.yaml`
2. Verifica los selectores visitando la página web manualmente

### El scraper solo extrae algunos proyectos

Verifica:
1. Que la paginación esté funcionando (revisa los logs)
2. Que no haya un filtro de legislatura activo
3. Los logs para ver si hay errores específicos

### Ver logs detallados

```bash
# Local
# Los logs aparecen en la consola donde ejecutaste uvicorn

# Docker
make docker-logs

# O con más detalle:
docker logs scraper-api -f
```

## 📚 Próximos Pasos

1. **Explorar la API**: Visita http://localhost:8000/docs
2. **Ejecutar tests**: `make test`
3. **Personalizar configuración**: Edita `config/colombia.yaml`
4. **Agregar más países**: Crea nuevos scrapers en `app/dominios/`

## 🆘 Ayuda

Si encuentras problemas:

1. Revisa los logs con `make docker-logs` o en la consola
2. Verifica que Chrome/ChromeDriver estén instalados
3. Asegúrate de que la URL del sitio web no haya cambiado
4. Consulta la documentación en `README.md`

## 🎯 Comandos Útiles

```bash
make help              # Ver todos los comandos disponibles
make docker-up         # Levantar servicios
make docker-down       # Detener servicios
make docker-restart    # Reiniciar servicios
make test              # Ejecutar tests
make clean             # Limpiar archivos temporales
```
