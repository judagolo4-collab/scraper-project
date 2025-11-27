# 🏛️ Sistema de Scraping y ETL de Proyectos Legislativos

## 📋 Objetivo del Repositorio

Sistema automatizado para **extraer, clasificar y almacenar proyectos de ley** de diferentes países. Actualmente implementado para Colombia (Cámara de Representantes), con arquitectura modular para fácil expansión a otros países e instituciones.

---

## 🎯 Arquitectura General

<img width="1786" height="765" alt="imagen" src="https://github.com/user-attachments/assets/c362c19a-79ea-4594-bcbc-439fda26b29e" />


<!-- Agregar imagen mostrando: Scraper API → S3 → Airflow → PostgreSQL -->

---

## 🏗️ Estructura del Proyecto

```
scraper-project/
│
├── scraper-service/              # 🔹 Servicio de Scraping (FastAPI)
│   ├── app/
│   │   ├── api/routes.py        # Endpoints REST
│   │   ├── scrapers/            # Scrapers modulares
│   │   │   ├── base.py          # Clase base
│   │   │   ├── selenium.py      # Scraper con Selenium
│   │   │   └── helpers.py       # Utilidades reutilizables
│   │   ├── dominios/
│   │   │   └── camara/
│   │   │       └── colombia.py  # Scraper específico Colombia
│   │   ├── services/
│   │   │   └── gemini_service.py # Clasificación con IA
│   │   └── utils/
│   │       ├── config_loader.py  # Carga de configuraciones
│   │       └── scraper_factory.py # Factory pattern
│   └── Dockerfile
│
├── airflow/                      # 🔹 Pipeline ETL (Airflow)
│   ├── dags/
│   │   └── congreso/
│   │       └── legislative_projects_etl.py  # DAG principal
│   ├── conexiones/              # Clientes para servicios externos
│   │   ├── AWS/s3_client.py     # Cliente S3
│   │   ├── SQL/postgres_client.py # Cliente PostgreSQL
│   │   └── scraper_service/http_client.py # Cliente HTTP
│   ├── Dockerfile
│   └── requirements.txt
│
├── config/
│   └── colombia.json            # Configuración por país
│
├── docker-compose.yml           # Orquestación de servicios
└── .env                         # Variables de entorno
```

---

## 🎯 Componentes del Sistema

### 1️⃣ **Servicio de Scraping** (Puerto 8000)

**Objetivo**: Extraer proyectos de ley de sitios web legislativos y clasificarlos por sector económico usando IA.

**Tecnologías**:
- FastAPI (API REST)
- Selenium (scraping dinámico)
- Gemini AI (clasificación de proyectos)
- User-agents rotativos (anti-bot)

**Características**:
- ✅ Scraping modular y parametrizable
- ✅ Clasificación automática en 21 sectores económicos con Gemini AI
- ✅ Configuración por país/institución (JSON)
- ✅ Factory pattern para fácil extensión

### 2️⃣ **Pipeline ETL con Airflow** (Puerto 8080)

**Objetivo**: Orquestar el proceso de extracción, transformación y carga de datos de forma automatizada y programable.

**Tecnologías**:
- Apache Airflow 2.10.4
- PostgreSQL (almacenamiento)
- LocalStack S3 (data lake local)
- Celery (ejecución distribuida)

**Características**:
- ✅ Carga incremental (evita duplicados)
- ✅ Auditoría completa (raw data en S3)
- ✅ Metadata de ejecuciones
- ✅ Programación flexible (daily, weekly, etc.)

---

## 🔌 Endpoints del Servicio de Scraping

### **Base URL**: `http://localhost:8000`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del servicio |
| `/docs` | GET | Documentación interactiva (Swagger) |
| `/api/scrape/colombia` | POST | Scrapea proyectos de Colombia |
| `/api/gemini/sectores` | GET | Lista sectores económicos disponibles |
| `/api/scrapers/available` | GET | Lista scrapers disponibles |
| `/api/config/{country}` | GET | Obtiene configuración de un país |

### Ejemplo de Uso

```bash
# Listar sectores económicos de Gemini
curl http://localhost:8000/api/gemini/sectores

# Scrapear 1 página de Colombia con clasificación IA
curl -X POST "http://localhost:8000/api/scrape/colombia?max_pages=1&classify=true"

# Ver documentación interactiva
open http://localhost:8000/docs
```

### Parámetros del Endpoint de Scraping

| Parámetro | Tipo | Descripción | Default |
|-----------|------|-------------|---------|
| `max_pages` | int | Número máximo de páginas a scrapear | Todas |
| `classify` | bool | Clasificar con Gemini AI | `true` |
| `legislatura` | string | Filtrar por legislatura (ej: "2025-2026") | Ninguno |
| `fecha_inicio` | string | Fecha límite (DD-MM-YYYY) | Ninguno |

---

## 🔄 Funcionamiento del DAG de Airflow

### **DAG**: `legislative_projects_etl`

**Ubicación**: `airflow/dags/congreso/legislative_projects_etl.py`

**Objetivo**: Extraer proyectos de ley, almacenarlos en S3 y PostgreSQL de forma incremental.

<img width="404" height="609" alt="imagen" src="https://github.com/user-attachments/assets/133c0dba-eb8b-4952-8602-8cb746622333" />


### Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────┐
│  1. EXTRACT                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Consulta al Scraper API                           │   │
│  │ • Endpoint: /api/scrape/colombia?classify=true      │   │
│  │ • Obtiene proyectos con clasificación Gemini        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. UPLOAD RAW TO S3                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Sube JSON completo a S3 (LocalStack)              │   │
│  │ • Bucket: scraper-raw-data                          │   │
│  │ • Path: colombia/camara/YYYY-MM-DD_HH-MM-SS.json    │   │
│  │ • Propósito: Auditoría y versionado                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. TRANSFORM                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Limpia y normaliza datos                          │   │
│  │ • Valida campos requeridos                          │   │
│  │ • Prepara estructura para PostgreSQL                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. LOAD TO POSTGRESQL                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • CARGA INCREMENTAL                                 │   │
│  │ • Usa UNIQUE(numero_camara, pais, camara)          │   │
│  │ • Solo inserta proyectos nuevos                     │   │
│  │ • Registra metadata de ejecución                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Tablas en PostgreSQL

**`proyectos_legislativos`**: Proyectos de ley
- Campos principales: `numero_camara`, `titulo`, `sector_economico`, `autores`, `estado`
- Incluye clasificación de Gemini AI
- UNIQUE constraint evita duplicados

**`ejecuciones_etl`**: Metadata de ejecuciones
- Registra: fecha, total extraído, nuevos insertados, ruta S3, estado

---

## 🤖 Clasificación con Gemini AI

El sistema usa **Google Gemini 2.0 Flash** para clasificar automáticamente cada proyecto en uno de **21 sectores económicos**:

- Minero-Energético
- Agricultura y Desarrollo Rural
- Tecnología y Telecomunicaciones
- Servicios Financieros
- Salud y Seguridad Social
- Educación
- Transporte e Infraestructura
- Comercio e Industria
- Turismo y Cultura
- Medio Ambiente
- Justicia y Seguridad
- Laboral y Empleo
- Tributario y Fiscal
- Vivienda y Desarrollo Urbano
- Defensa y Fuerzas Armadas
- Y más...

**Endpoint para ver todos**: `GET /api/gemini/sectores`

---

## 🚀 Cómo Levantar los Servicios

### Prerequisitos

- Docker Desktop instalado y corriendo
- Al menos 8GB RAM disponibles
- Archivo `.env` en la raíz con:
  ```env
  GEMINI_API_KEY=tu_api_key_aqui
  ```

### Paso 1: Levantar Infraestructura Base

```bash
cd scraper-project

# Levantar PostgreSQL, Redis, LocalStack y Scraper API
docker-compose up -d postgres redis localstack scraper-api

# Esperar 20 segundos
sleep 20

# Verificar que estén healthy
docker-compose ps
```

### Paso 2: Inicializar Airflow (Solo Primera Vez)

```bash
# Inicializar base de datos de Airflow
docker-compose up airflow-init

# Esperar a ver: "Airflow initialized successfully!"
```

### Paso 3: Levantar Airflow

```bash
# Levantar todos los servicios de Airflow
docker-compose up -d airflow-webserver airflow-scheduler airflow-worker

# Esperar 30 segundos
sleep 30

# Verificar que todo esté healthy
docker-compose ps
```

### Paso 4: Acceder a las Interfaces

**Airflow UI**:
```
URL: http://localhost:8080
Usuario: admin
Contraseña: admin
```

**Scraper API (Swagger)**:
```
URL: http://localhost:8000/docs
```

### Paso 5: Ejecutar el DAG

1. Ir a http://localhost:8080
2. Login: `admin` / `admin`
3. Buscar DAG: `legislative_projects_etl`
4. Activar (toggle switch a ON)
5. Ejecutar manualmente: Botón "Play" → "Trigger DAG"
6. Monitorear progreso en tiempo real

---

## 🧪 Verificar que Funciona

### Verificar Datos en S3

```bash
# Listar archivos
docker exec localstack-s3 awslocal s3 ls s3://scraper-raw-data/colombia/camara/

# Ver contenido de un archivo
docker exec localstack-s3 awslocal s3 cp \
  s3://scraper-raw-data/colombia/camara/<archivo>.json \
  /tmp/test.json
docker exec localstack-s3 cat /tmp/test.json
```

### Verificar Datos en PostgreSQL

```bash
# Conectar a la base de datos
docker exec -it postgres-db psql -U airflow -d proyectos_ley

# Ver proyectos
SELECT numero_camara, titulo, sector_economico 
FROM proyectos_legislativos 
LIMIT 5;

# Ver ejecuciones del ETL
SELECT * FROM ejecuciones_etl 
ORDER BY fecha_ejecucion DESC;

# Salir
\q
```

---

## 🛠️ Comandos Útiles

### Detener Todo
```bash
docker-compose down
```

### Ver Logs
```bash
# Todos los servicios
docker-compose logs -f

# Un servicio específico
docker-compose logs -f airflow-scheduler
docker-compose logs -f scraper-api
```

### Reiniciar un Servicio
```bash
docker-compose restart scraper-api
docker-compose restart airflow-scheduler
```

### Estado de los Servicios
```bash
docker-compose ps
```

---

## 📊 Servicios y Puertos

| Servicio | Puerto | URL | Descripción |
|----------|--------|-----|-------------|
| **Airflow UI** | 8080 | http://localhost:8080 | Interfaz web de Airflow |
| **Scraper API** | 8000 | http://localhost:8000/docs | API REST + Swagger |
| **PostgreSQL** | 5432 | `localhost:5432` | Base de datos |
| **Redis** | 6379 | `localhost:6379` | Cache y Celery backend |
| **LocalStack (S3)** | 4566 | `localhost:4566` | S3 local |

---

## 🔮 Próximos Pasos

### Agregar Nuevo País

1. Crear archivo `config/peru.json` con la configuración
2. Crear scraper en `scraper-service/app/dominios/congreso/peru.py`
3. Registrar en el factory (`scraper_factory.py`)
4. El DAG ya es genérico, funcionará automáticamente

### Expansión del Sistema

- Agregar más países (Perú, Chile, México, etc.)
- Implementar notificaciones (Slack, Email)
- Dashboard con Grafana para visualización
- Despliegue en producción (AWS/GCP/Azure)

---

## 📄 Licencia

MIT

---

## 👥 Contribuciones

Para contribuir al proyecto:
1. Fork el repositorio
2. Crea una rama con tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

