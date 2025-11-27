# 🕷️ Scraper de Proyectos de Ley - Colombia

Sistema modular de scraping para extraer información de proyectos de ley de la Cámara de Representantes de Colombia.

## 📋 Características

- ✅ Arquitectura modular y reutilizable
- ✅ Soporte para contenido dinámico con Selenium (modo headless)
- ✅ Paginación automática
- ✅ Extracción de PDFs y metadatos
- ✅ Filtrado por legislatura
- ✅ API REST con FastAPI
- ✅ Base de datos PostgreSQL
- ✅ Dockerizado

## 🏗️ Estructura del Proyecto

```
scraper/
├── docker/                      # Configuración Docker
├── scraper-service/             # Microservicio FastAPI
│   ├── app/
│   │   ├── main.py             # Entry point
│   │   ├── api/                # Endpoints REST
│   │   ├── dominios/           # Scrapers específicos por país
│   │   │   └── camara/
│   │   │       └── colombia.py # Scraper Colombia - Cámara
│   │   ├── scrapers/           # Clases base reutilizables
│   │   │   ├── base.py        # Clase abstracta base
│   │   │   └── selenium.py    # Scraper con Selenium
│   │   └── utils/             # Utilidades
│   └── tests/                 # Tests unitarios e integración
├── database/                   # Migraciones y modelos
└── config/                    # Configuraciones YAML
```

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.11+
- Docker y Docker Compose
- ChromeDriver (para Selenium)

### Instalación Local

```bash
# Clonar el repositorio
cd scraper-service

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servicio
uvicorn app.main:app --reload
```

### Con Docker

```bash
cd docker
docker-compose up --build
```

## 📊 Datos Extraídos

Para cada proyecto de ley se extrae:

- **Título del proyecto**
- **Número de Cámara y Senado**
- **Fecha de radicación**
- **Resumen/Exposición de motivos**
- **Estado actual**
- **Tipo de ley**
- **Autores**
- **Comisión**
- **Legislatura**
- **Origen**
- **Enlace al PDF del proyecto**
- **Enlace a la Gaceta**

## 🔧 Configuración

La configuración se maneja mediante archivos YAML en `config/`:

```yaml
# config/colombia.yaml
pais: "Colombia"
institucion: "Camara"
url: "https://www.camara.gov.co/secretaria/proyectos-de-ley#menu"
selenium:
  wait_time: 10
  driver_path: "/usr/bin/chromedriver"
selectors:
  tabla_proyectos: "table.proyectos-table tbody tr"
  paginacion_siguiente: "button.pagina-btn[data-pagina='next']"
  # ... más selectores
```

## 📡 API Endpoints

```
GET  /api/scrape/colombia        # Ejecutar scraping de Colombia
GET  /api/proyectos              # Listar proyectos almacenados
GET  /api/proyectos/{id}         # Obtener proyecto específico
POST /api/scrape/colombia/filter # Scraping con filtros (legislatura)
```

## 🧪 Testing

```bash
# Tests unitarios
pytest tests/unit/

# Tests de integración
pytest tests/integration/

# Cobertura
pytest --cov=app tests/
```

## 📝 Licencia

MIT

## 👥 Contribución

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios propuestos.
