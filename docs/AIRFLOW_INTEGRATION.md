# ✅ PROYECTO AIRFLOW COMPLETADO

## 🎉 Sistema ETL Completo con Airflow

He creado un sistema profesional de ETL con Airflow que se integra perfectamente con tu scraper.

---

## 🏗️ LO QUE SE CREÓ

### 1. ✅ Docker Compose Unificado

**Un solo comando levanta TODO**:
```bash
docker-compose up -d
```

**8 servicios**:
1. `scraper-api` - Tu servicio FastAPI con Gemini
2. `postgres` - Base de datos transaccional
3. `localstack` - S3 local (AWS simulado)
4. `redis` - Backend de Celery
5. `airflow-webserver` - UI de Airflow (http://localhost:8080)
6. `airflow-scheduler` - Scheduler de DAGs
7. `airflow-worker` - Workers de Celery
8. `airflow-init` - Inicialización automática

### 2. ✅ DAG: legislative_projects_etl

**Flujo completo**:
```
1. Check Services (health check)
2. Extract Data (consulta scraper-api)
3. Save to S3 Raw (guarda raw data)
4. Process Data (organiza datos)
5. Save to PostgreSQL (guarda transaccional)
```

**Características**:
- ✅ **Carga incremental** - Solo nuevos proyectos
- ✅ **Multi-país** - Fácil agregar más fuentes
- ✅ **Clasificación IA** - Gemini automático
- ✅ **Upsert** - INSERT ... ON CONFLICT UPDATE
- ✅ **Metadata** - Tracking de ejecuciones

### 3. ✅ Clientes Reutilizables

**`airflow/conexiones/`**:
- `AWS/s3_client.py` - Cliente S3 (LocalStack)
- `SQL/postgres_client.py` - Cliente PostgreSQL
- `scraper_service/http_client.py` - Cliente HTTP

### 4. ✅ Base de Datos

**Tablas creadas automáticamente**:
- `proyectos` - Datos de proyectos de ley
- `scraper_metadata` - Metadata de ejecuciones

**Características**:
- UNIQUE constraint (numero_camara, pais, institucion)
- Índices optimizados
- Upsert automático

### 5. ✅ LocalStack S3

**Buckets creados**:
- `scraper-raw-data` - Datos raw
- `scraper-processed-data` - Datos procesados

**Estructura**:
```
s3://scraper-raw-data/
  └─ colombia/camara/2024/11/27/data_143025.json
```

---

## 🚀 CÓMO USAR

### 1. Levantar Todo

```bash
# Desde la raíz del proyecto
docker-compose up -d --build

# Ver logs
docker-compose logs -f
```

### 2. Acceder a Airflow

```bash
# Abrir UI
open http://localhost:8080

# Usuario: admin
# Password: admin
```

### 3. Ejecutar DAG

**Opción 1: Automático** (diario a las 2 AM)
- El DAG se ejecutará automáticamente

**Opción 2: Manual**
- En Airflow UI, click en el botón "Play" del DAG

**Opción 3: CLI**
```bash
docker-compose exec airflow-scheduler airflow dags trigger legislative_projects_etl
```

### 4. Verificar Resultados

```bash
# Ver en PostgreSQL
docker-compose exec postgres psql -U airflow -d proyectos_ley -c "SELECT * FROM proyectos LIMIT 5;"

# Ver metadata
docker-compose exec postgres psql -U airflow -d proyectos_ley -c "SELECT * FROM scraper_metadata ORDER BY execution_date DESC;"

# Ver en S3 (LocalStack)
awslocal --endpoint-url=http://localhost:4566 s3 ls s3://scraper-raw-data/ --recursive
```

---

## 📁 ESTRUCTURA CREADA

```
scraper-project/
│
├── docker-compose.yml        ← TODO en un archivo
├── AIRFLOW_README.md         ← Documentación de Airflow
│
├── scraper-service/          ← Tu scraper (sin cambios)
│
├── airflow/                  ← NUEVO
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── dags/
│   │   └── congreso/
│   │       └── legislative_projects_etl.py  ← DAG principal
│   ├── conexiones/
│   │   ├── AWS/
│   │   │   └── s3_client.py
│   │   ├── SQL/
│   │   │   └── postgres_client.py
│   │   └── scraper_service/
│   │       └── http_client.py
│   └── logs/
│
└── docker/
    ├── init-multiple-dbs.sh  ← Crea DBs
    └── init-localstack.sh    ← Crea buckets S3
```

---

## 🔄 CARGA INCREMENTAL

### Cómo Funciona

1. **Primera ejecución** (ej: 2024-01-01)
   - Extrae TODOS los proyectos históricos
   - Guarda en S3 y PostgreSQL
   - Registra fecha: 2024-01-01

2. **Segunda ejecución** (ej: 2024-01-02)
   - Consulta última fecha exitosa: 2024-01-01
   - Pasa `fecha_inicio=01-01-2024` al scraper
   - Scraper solo extrae proyectos desde esa fecha
   - Se detiene al encontrar proyectos antiguos
   - Solo inserta/actualiza proyectos nuevos

3. **Siguientes ejecuciones**
   - Siempre usa la última fecha exitosa
   - Solo procesa datos nuevos/actualizados

### Ventajas

✅ **Eficiente** - No reprocesa data histórica  
✅ **Rápido** - Solo nuevos proyectos  
✅ **Económico** - Menos tokens de Gemini  
✅ **Escalable** - Funciona con miles de proyectos  

---

## 🆕 AGREGAR NUEVO PAÍS

### Super Fácil (5 minutos)

**1. Crear scraper** (si no existe)
```python
# En scraper-service/app/dominios/
# Ver docs/QUICKSTART.md
```

**2. Agregar al DAG**
```python
# Editar airflow/dags/congreso/legislative_projects_etl.py

DATA_SOURCES = [
    {
        'country': 'colombia',
        'institution': 'camara',
        'max_pages': None,
        'classify': True
    },
    {
        'country': 'peru',         # ← NUEVO
        'institution': 'congreso',
        'max_pages': None,
        'classify': True
    },
]
```

**3. Reiniciar**
```bash
docker-compose restart airflow-scheduler
```

**¡Listo!** El DAG automáticamente procesa el nuevo país.

---

## 📊 MONITOREO

### Airflow UI
- **URL**: http://localhost:8080
- Ver ejecuciones, logs, métricas
- Gráfico de tareas
- Historial completo

### PostgreSQL
```sql
-- Última ejecución
SELECT * FROM scraper_metadata 
ORDER BY execution_date DESC LIMIT 1;

-- Proyectos por país
SELECT pais, COUNT(*) FROM proyectos GROUP BY pais;

-- Proyectos por sector
SELECT sector_economico, COUNT(*) 
FROM proyectos 
GROUP BY sector_economico 
ORDER BY COUNT(*) DESC;
```

### S3 (LocalStack)
```bash
awslocal --endpoint-url=http://localhost:4566 s3 ls s3://scraper-raw-data/ --recursive
```

---

## 🎯 CARACTERÍSTICAS DESTACADAS

### 1. Carga Incremental Automática
```python
# El DAG automáticamente:
1. Consulta última fecha exitosa
2. Pasa al scraper como fecha_inicio
3. Solo procesa nuevos/actualizados
4. Upsert en PostgreSQL
```

### 2. Data Lake + Data Warehouse
```
Raw Data (S3) → Processed Data (S3) → Transactional (PostgreSQL)
     ↓                    ↓                      ↓
  Inmutable          Transformado           Consultas rápidas
```

### 3. Multi-Fuente
```python
# Agregar país = editar lista
DATA_SOURCES = [
    {'country': 'colombia', ...},
    {'country': 'peru', ...},
    {'country': 'argentina', ...},  # Solo agregar
]
```

### 4. Observabilidad
- ✅ Logs centralizados
- ✅ Metadata de ejecuciones
- ✅ UI de Airflow
- ✅ Métricas en PostgreSQL

---

## 🔧 COMANDOS ÚTILES

### Docker
```bash
# Levantar todo
docker-compose up -d

# Ver logs
docker-compose logs -f airflow-scheduler

# Reiniciar servicio
docker-compose restart airflow-scheduler

# Detener todo
docker-compose down

# Limpiar (⚠️ borra datos)
docker-compose down -v
```

### Airflow
```bash
# Trigger manual
docker-compose exec airflow-scheduler airflow dags trigger legislative_projects_etl

# Ver DAGs
docker-compose exec airflow-scheduler airflow dags list

# Pausar/Despausar
docker-compose exec airflow-scheduler airflow dags pause legislative_projects_etl
docker-compose exec airflow-scheduler airflow dags unpause legislative_projects_etl
```

### PostgreSQL
```bash
# Conectar
docker-compose exec postgres psql -U airflow -d proyectos_ley

# Ver proyectos
SELECT * FROM proyectos ORDER BY fecha_extraccion DESC LIMIT 10;

# Contar por país
SELECT pais, COUNT(*) FROM proyectos GROUP BY pais;
```

---

## ✅ CHECKLIST DE LO QUE TIENES

```
✓ Docker Compose unificado (1 comando para todo)
✓ Scraper Service (FastAPI + Gemini)
✓ Airflow (Webserver + Scheduler + Worker)
✓ PostgreSQL (2 DBs: airflow + proyectos_ley)
✓ LocalStack (S3 local)
✓ Redis (Celery backend)
✓ DAG con carga incremental
✓ Clientes reutilizables (S3, PostgreSQL, HTTP)
✓ Base de datos con índices
✓ Upsert automático
✓ Metadata tracking
✓ Documentación completa
✓ Scripts de inicialización
```

---

## 🎉 RESULTADO FINAL

### Antes
- Scraper standalone
- Sin orquestación
- Sin almacenamiento
- Ejecución manual

### Ahora
- ✅ **Sistema ETL completo**
- ✅ **Orquestación con Airflow**
- ✅ **Data Lake (S3) + Data Warehouse (PostgreSQL)**
- ✅ **Carga incremental automática**
- ✅ **Multi-país listo**
- ✅ **Monitoreo y observabilidad**
- ✅ **Todo en Docker Compose**

---

## 📚 DOCUMENTACIÓN

| Archivo | Propósito |
|---------|-----------|
| `AIRFLOW_README.md` | **Documentación completa de Airflow** |
| `README.md` | Documentación del scraper |
| `docs/` | Guías técnicas |

---

<div align="center">

## 🚀 ¡SISTEMA COMPLETO LISTO!

**1 comando → 8 servicios → ETL completo**

```bash
docker-compose up -d
```

</div>

