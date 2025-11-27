# Guía de Pruebas del Proyecto

## ✅ Estado Actual de la Integración

### Servicios Creados

1. **PostgreSQL** (puerto 5432)
   - Base de datos `airflow` - Para metadata de Airflow
   - Base de datos `proyectos_ley` - Para datos procesados
   - Base de datos `scraper_metadata` - Para metadata del scraper
   - ✅ **PROBADO Y FUNCIONANDO**

2. **Redis** (puerto 6379)
   - Para Celery (executor de Airflow)
   - ✅ **PROBADO Y FUNCIONANDO**

3. **LocalStack** (puerto 4566)
   - Buckets S3: `scraper-raw-data`, `scraper-processed-data`
   - ✅ **PROBADO Y FUNCIONANDO**

4. **Scraper API** (puerto 8000)
   - API FastAPI con scrapers y Gemini
   - ⏳ **PENDIENTE DE PRUEBA**

5. **Airflow** (puerto 8080)
   - Webserver, Scheduler, Worker, Triggerer
   - ⏳ **PENDIENTE DE PRUEBA**

---

## 🚀 Cómo Levantar Todos los Servicios

### Prerequisitos

1. **Docker Desktop** debe estar corriendo completamente
   - Verificar que el icono esté verde/activo
   - En la ventana debe decir "Engine running"

2. **Archivo `.env`** en la raíz del proyecto con:
   ```bash
   GEMINI_API_KEY=AIzaSyAjFBkDoLwGL7DPNO_Z7rSW1fK6IhX3jxY
   ```

### Paso 1: Levantar Infraestructura Base

```bash
cd /Users/juandagomezl/Documents/Personal/scraper-project/scraper-project

# Levantar PostgreSQL, Redis y LocalStack
docker-compose up -d postgres redis localstack

# Esperar a que estén healthy (15-20 segundos)
sleep 20

# Verificar estado
docker-compose ps
```

**Resultado esperado**: Los 3 servicios deben estar con estado `(healthy)`

### Paso 2: Verificar Infraestructura

```bash
# Verificar buckets S3
docker exec localstack-s3 awslocal s3 ls

# Verificar bases de datos PostgreSQL
docker exec postgres-db psql -U airflow -l
```

**Resultado esperado**:
- S3: Debe mostrar 2 buckets (`scraper-raw-data`, `scraper-processed-data`)
- PostgreSQL: Debe mostrar 4 bases de datos (`airflow`, `proyectos_ley`, `scraper_metadata`, `postgres`, `template0`, `template1`)

### Paso 3: Levantar Scraper API

```bash
# Levantar el scraper
docker-compose up -d scraper-api

# Esperar a que se levante (10 segundos)
sleep 10

# Verificar logs
docker-compose logs scraper-api --tail=50
```

### Paso 4: Probar Scraper API

```bash
# Probar endpoint de salud
curl http://localhost:8000/health

# Probar scraping de Colombia (sin clasificación)
curl http://localhost:8000/api/scrape/colombia?max_items=2

# Probar scraping con clasificación de Gemini
curl "http://localhost:8000/api/scrape/colombia?max_items=2&classify=true"

# Ver sectores disponibles
curl http://localhost:8000/api/gemini/sectores
```

### Paso 5: Inicializar Airflow

```bash
# Inicializar base de datos de Airflow
docker-compose up airflow-init

# Esperar a que termine (puede tardar 1-2 minutos)
# Debe mostrar "Airflow initialized successfully!"
```

### Paso 6: Levantar Airflow

```bash
# Levantar todos los servicios de Airflow
docker-compose up -d airflow-webserver airflow-scheduler airflow-worker

# Esperar a que se levanten (30 segundos)
sleep 30

# Verificar estado
docker-compose ps
```

### Paso 7: Acceder a Airflow

1. Abrir navegador en: http://localhost:8080
2. **Usuario**: `admin`
3. **Contraseña**: `admin`
4. Buscar el DAG: `legislative_projects_etl`
5. Activarlo y ejecutarlo manualmente

---

## 🧪 Pruebas Funcionales del DAG

### Flujo del DAG

El DAG `legislative_projects_etl` realiza:

1. **Extract**: Consulta el scraper API en `/api/scrape/colombia?classify=true`
2. **Upload Raw**: Sube el JSON completo a S3 bucket `scraper-raw-data`
3. **Transform**: Organiza los datos y crea estructura para PostgreSQL
4. **Load**: Guarda en PostgreSQL de forma **incremental** (solo nuevos proyectos)

### Verificar que Funciona

#### 1. Ver datos en S3

```bash
# Listar archivos en el bucket raw
docker exec localstack-s3 awslocal s3 ls s3://scraper-raw-data/

# Descargar y ver un archivo
docker exec localstack-s3 awslocal s3 cp s3://scraper-raw-data/colombia/camara/YYYY-MM-DD_HH-MM-SS.json /tmp/test.json
docker exec localstack-s3 cat /tmp/test.json
```

#### 2. Ver datos en PostgreSQL

```bash
# Conectarse a la base de datos
docker exec -it postgres-db psql -U airflow -d proyectos_ley

# Ver tablas creadas
\dt

# Ver datos
SELECT * FROM proyectos_legislativos LIMIT 5;

# Ver metadatos de ejecución
SELECT * FROM ejecuciones_etl ORDER BY fecha_ejecucion DESC LIMIT 5;

# Salir
\q
```

#### 3. Verificar Carga Incremental

```bash
# Ejecutar el DAG 2 veces seguidas desde la UI de Airflow
# La segunda vez debe:
# - Detectar que ya existen proyectos
# - Solo insertar nuevos (si los hay)
# - Registrar en la tabla de metadatos cuántos se procesaron

# Verificar en PostgreSQL
docker exec -it postgres-db psql -U airflow -d proyectos_ley -c "SELECT * FROM ejecuciones_etl ORDER BY fecha_ejecucion DESC LIMIT 3;"
```

---

## 🔧 Comandos Útiles

### Ver logs de un servicio

```bash
# Scraper
docker-compose logs -f scraper-api

# Airflow Scheduler
docker-compose logs -f airflow-scheduler

# Airflow Worker
docker-compose logs -f airflow-worker

# Todos
docker-compose logs -f
```

### Reiniciar un servicio

```bash
docker-compose restart scraper-api
docker-compose restart airflow-scheduler
```

### Detener todo

```bash
docker-compose down
```

### Detener y limpiar todo (incluye volúmenes)

```bash
docker-compose down -v
```

### Reconstruir una imagen

```bash
# Scraper
docker-compose build scraper-api

# Airflow
docker-compose build airflow-webserver
```

---

## 📊 Estructura de Datos en PostgreSQL

### Tabla: `proyectos_legislativos`

```sql
CREATE TABLE proyectos_legislativos (
    id SERIAL PRIMARY KEY,
    numero_camara VARCHAR(50),
    numero_senado VARCHAR(50),
    titulo TEXT NOT NULL,
    url_detalle TEXT,
    tipo VARCHAR(100),
    autores TEXT,
    estado VARCHAR(100),
    origen VARCHAR(50),
    comision VARCHAR(200),
    legislatura VARCHAR(50),
    fecha_radicacion DATE,
    resumen TEXT,
    url_pdf TEXT,
    url_gaceta TEXT,
    sector_economico VARCHAR(100),
    pais VARCHAR(50) DEFAULT 'colombia',
    camara VARCHAR(50) DEFAULT 'camara',
    fecha_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(numero_camara, pais, camara)
);
```

### Tabla: `ejecuciones_etl`

```sql
CREATE TABLE ejecuciones_etl (
    id SERIAL PRIMARY KEY,
    dag_id VARCHAR(100) NOT NULL,
    run_id VARCHAR(200) NOT NULL,
    fecha_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pais VARCHAR(50),
    camara VARCHAR(50),
    total_proyectos_extraidos INTEGER,
    proyectos_nuevos_insertados INTEGER,
    proyectos_actualizados INTEGER,
    ruta_s3_raw TEXT,
    estado VARCHAR(50),
    mensaje_error TEXT
);
```

---

## ❗ Troubleshooting

### Docker no conecta

```bash
# Verificar contexto
docker context ls

# Usar el correcto
docker context use desktop-linux

# Verificar que funcione
docker ps
```

### Puerto ocupado

```bash
# Ver qué está usando el puerto (ej: 8000)
lsof -i :8000

# Matar el proceso
kill -9 <PID>
```

### Airflow no se levanta

```bash
# Ver logs
docker-compose logs airflow-init

# Si falla, limpiar y volver a inicializar
docker-compose down -v
docker volume prune
docker-compose up airflow-init
```

### LocalStack falla

```bash
# Ver logs
docker-compose logs localstack

# Si hay problemas con /tmp/localstack
docker-compose down
docker volume rm scraper-project_localstack-data
docker-compose up -d localstack
```

---

## 📝 Notas Importantes

1. **Orden de inicio**: Siempre levantar en orden: postgres/redis/localstack → scraper-api → airflow-init → airflow services

2. **Primera vez**: `airflow-init` solo se ejecuta una vez para crear el usuario admin

3. **Datos incrementales**: El DAG usa `UNIQUE(numero_camara, pais, camara)` para evitar duplicados

4. **Gemini API**: La clasificación puede tardar unos segundos adicionales

5. **Logs**: Si algo falla, siempre revisar logs con `docker-compose logs <servicio>`

