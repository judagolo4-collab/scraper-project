# 🐳 Docker - Configuración y Orquestación

Esta carpeta contiene **toda la configuración Docker** del proyecto.

## 📁 Estructura

```
docker/
├── docker-compose.yml          # Orquestación de todos los servicios
├── scraper-api/
│   └── Dockerfile             # Imagen del scraper (FastAPI + Selenium)
├── airflow/
│   └── Dockerfile             # Imagen de Airflow
└── init-scripts/
    ├── init-multiple-dbs.sh   # Inicializa bases de datos PostgreSQL
    └── init-localstack.sh     # Inicializa buckets S3 en LocalStack
```

## 🚀 Uso

### Levantar Todos los Servicios

**Opción 1: Desde la raíz (Recomendado)**
```bash
docker-compose -f docker/docker-compose.yml --env-file .env up -d
```

**Opción 2: Desde la carpeta docker/**
```bash
cd docker/
docker-compose --env-file ../.env up -d
```

### Levantar Servicios Específicos

```bash
# Desde la raíz (agregar --env-file .env):
# Solo infraestructura
docker-compose -f docker/docker-compose.yml --env-file .env up -d postgres redis localstack

# Solo scraper
docker-compose -f docker/docker-compose.yml --env-file .env up -d scraper-api

# Solo Airflow
docker-compose -f docker/docker-compose.yml --env-file .env up -d airflow-webserver airflow-scheduler airflow-worker
```

### Ver Estado

```bash
# Desde la raíz:
docker-compose -f docker/docker-compose.yml --env-file .env ps

# O desde docker/:
cd docker/ && docker-compose --env-file ../.env ps
```

### Ver Logs

```bash
# Desde la raíz:
# Todos los servicios
docker-compose -f docker/docker-compose.yml --env-file .env logs -f

# Servicio específico
docker-compose -f docker/docker-compose.yml --env-file .env logs -f airflow-scheduler
```

### Detener Todo

```bash
# Desde la raíz:
docker-compose -f docker/docker-compose.yml --env-file .env down

# O desde docker/:
cd docker/ && docker-compose --env-file ../.env down
```

### Reconstruir Imágenes

```bash
# Desde la raíz:
# Reconstruir todo
docker-compose -f docker/docker-compose.yml --env-file .env build --no-cache

# Reconstruir un servicio
docker-compose -f docker/docker-compose.yml --env-file .env build --no-cache scraper-api
```

## 🏗️ Servicios Definidos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **scraper-api** | 8000 | FastAPI + Selenium + Gemini |
| **postgres** | 5432 | PostgreSQL (3 bases de datos) |
| **redis** | 6379 | Redis para Celery |
| **localstack** | 4566 | S3 local (LocalStack) |
| **airflow-webserver** | 8080 | UI de Airflow |
| **airflow-scheduler** | - | Scheduler de DAGs |
| **airflow-worker** | - | Worker Celery |

## 📝 Notas Importantes

1. **Variables de entorno**: Asegúrate de tener `.env` en la raíz con `GEMINI_API_KEY`
2. **Primera vez**: Ejecuta `docker-compose up airflow-init` antes de levantar Airflow
3. **Volúmenes**: Los datos persisten en volúmenes Docker
4. **Hot reload**: El scraper-api tiene hot reload activado para desarrollo

## 🔧 Troubleshooting

### Puerto ocupado
```bash
# Ver qué proceso usa el puerto
lsof -i :8000  # o el puerto que necesites

# Matar el proceso
kill -9 <PID>
```

### Limpiar todo
```bash
# Detener y eliminar contenedores, redes y volúmenes
docker-compose down -v

# Limpiar sistema Docker completo
docker system prune -a
```

### Reconstruir desde cero
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up airflow-init
docker-compose up -d
```

