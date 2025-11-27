# 🌪️ Airflow ETL Pipeline

Sistema de orquestación para la ingesta, procesamiento y almacenamiento de datos legislativos. Gestiona el ciclo de vida completo de los datos desde la extracción hasta el almacenamiento estructurado.

---

## 🔄 Flujos de Trabajo (DAGs)

Actualmente el sistema cuenta con un DAG principal modular y escalable:


### `multi_country_scraper`
Ejecuta el proceso ETL para todos los países configurados (Colombia y Perú) en paralelo.

<img width="693" height="483" alt="imagen" src="https://github.com/user-attachments/assets/da5cd202-e420-4deb-9da9-21a294f17a6d" />

<img width="2360" height="1036" alt="imagen" src="https://github.com/user-attachments/assets/f3bde461-3dbd-45a7-8904-84897f6e1783" />


**Pasos del Pipeline:**
1.  **Extract**: Llama al `Scraper Service` vía HTTP para obtener los datos crudos.
2.  **Load S3 (Raw Layer)**: Guarda la respuesta JSON original en un Data Lake (S3/LocalStack).
    *   Ruta: `raw/YYYY/MM/DD/{pais}/{numero_proyecto}.json`
    *   Garantiza inmutabilidad y auditoría.
3.  **Load PostgreSQL (Structured Layer)**: Procesa y guarda los datos en una base de datos relacional.
    *   Utiliza **UPSERT** (Insert on Conflict) para manejar duplicados y actualizaciones de estado.
    *   Mantiene un historial limpio y actualizado.
4.  **Summary**: Genera y loguea estadísticas de la ejecución.

---

## 🏗️ Estructura Modular

A diferencia de los DAGs tradicionales monolíticos, este proyecto utiliza una estructura modular avanzada:

```
airflow/
├── dags/                       # Solo definiciones de DAGs
│   └── multi_country_scraper.py
│
├── core/                       # Factories de Tareas
│   └── scraper_tasks.py        # Crea tareas estandarizadas (extract, s3, pg)
│
├── helpers/                    # Lógica de Negocio Reutilizable
│   ├── extractors.py           # Lógica de comunicación con API
│   ├── storage.py              # Lógica de guardado en S3 y DB
│   └── utils.py                # Utilidades generales
│
└── source/                     # Código Fuente SQL
    ├── init_tables.sql         # DDL de base de datos
    └── migrate_...sql          # Scripts de migración
```

**Ventajas:**
*   **Código Limpio**: El DAG principal tiene menos de 70 líneas.
*   **Reutilización**: La lógica de guardado en S3 es la misma para todos los países.
*   **Escalabilidad**: Agregar un país al DAG es tan simple como agregarlo a una lista `COUNTRIES`.

---

## 💾 Modelo de Datos

### PostgreSQL (`proyectos_ley`)

La tabla principal está diseñada para soportar múltiples países con un esquema flexible pero estructurado.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | Primary Key |
| `country` | VARCHAR | Identificador del país (colombia, peru) |
| `numero` | VARCHAR | ID único del proyecto en su país |
| `titulo` | TEXT | Título del proyecto |
| `estado` | VARCHAR | Estado actual (Presentado, Aprobado, etc.) |
| `sector_economico`| VARCHAR | Clasificación IA (Salud, Economía...) |
| `url_detalle` | VARCHAR | Link a la fuente original |
| `extracted_at` | TIMESTAMP| Fecha de extracción |

**Índices:** Optimizados para búsquedas por país, número, estado y fecha.

**Vistas:**
*   `stats_por_pais`: Estadísticas agregadas.
*   `proyectos_recientes`: Últimos proyectos ingresados.

---

## ⚙️ Configuración y Conexiones

Airflow se configura automáticamente mediante Docker Compose, pero utiliza estas conexiones internas:

1.  **`postgres_default`**: Conexión a la base de datos interna.
2.  **`aws_default`**: Conexión a LocalStack (emulación S3 local).

---

## 🚀 Comandos Útiles

```bash
# Entrar al contenedor de scheduler para debug
docker exec -it airflow-scheduler bash

# Listar tareas de un DAG
airflow tasks list multi_country_scraper

# Probar una tarea específica
airflow tasks test multi_country_scraper extract_colombia 2024-01-01
```
