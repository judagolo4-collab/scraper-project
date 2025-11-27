# 📚 Documentación del Proyecto

## 📖 Documentación Principal

Para comenzar, lee el **[README principal](../README.md)** que contiene:
- 🎯 Objetivo del repositorio
- 🏗️ Estructura del proyecto
- 🔌 Endpoints del servicio
- 🔄 Funcionamiento del DAG
- 🚀 Cómo levantar los servicios
- 🤖 Integración con Gemini AI

---

## 📂 Documentación Adicional

### Guías Detalladas

| Documento | Descripción |
|-----------|-------------|
| **[QUICKSTART.md](./QUICKSTART.md)** | Guía rápida para comenzar en 5 minutos |
| **[TESTING.md](./TESTING.md)** | Guía completa de pruebas y verificación |
| **[EXAMPLES.md](./EXAMPLES.md)** | Ejemplos de uso y casos prácticos |
| **[GEMINI.md](./GEMINI.md)** | Integración detallada con Gemini AI |
| **[AIRFLOW_INTEGRATION.md](./AIRFLOW_INTEGRATION.md)** | Detalles del DAG y pipeline ETL |

---

## 🚀 Inicio Rápido

### 1. Levantar Servicios

```bash
# Servicios base
docker-compose up -d postgres redis localstack scraper-api

# Inicializar Airflow (solo primera vez)
docker-compose up airflow-init

# Levantar Airflow
docker-compose up -d airflow-webserver airflow-scheduler airflow-worker
```

### 2. Acceder

- **Airflow**: http://localhost:8080 (admin/admin)
- **Scraper API**: http://localhost:8000/docs

### 3. Ejecutar DAG

1. Ir a Airflow UI
2. Buscar `legislative_projects_etl`
3. Activar y ejecutar

---

## 🎯 Estructura de la Documentación

```
docs/
├── README.md                    # Este archivo (índice)
├── QUICKSTART.md               # Inicio rápido
├── TESTING.md                  # Guía de pruebas
├── EXAMPLES.md                 # Ejemplos prácticos
├── GEMINI.md                   # Integración Gemini AI
└── AIRFLOW_INTEGRATION.md      # Detalles de Airflow
```

---

## 💡 Recomendación

**Si es tu primera vez**, empieza por:
1. Leer el [README principal](../README.md)
2. Seguir la [guía rápida](./QUICKSTART.md)
3. Ver [ejemplos de uso](./EXAMPLES.md)

**Para profundizar**, revisa:
- [Integración con Gemini AI](./GEMINI.md)
- [Pipeline de Airflow](./AIRFLOW_INTEGRATION.md)
- [Pruebas completas](./TESTING.md)

---

## 🤝 Contribuir

Para contribuir a la documentación:
1. Mantén la simplicidad
2. Incluye ejemplos prácticos
3. Actualiza este índice si agregas nuevos documentos

---

**¿Preguntas?** Abre un issue en el repositorio.
