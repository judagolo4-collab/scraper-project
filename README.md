# 🕷️ Legislative Scraper Project

Plataforma ETL moderna y modular para la extracción, procesamiento y análisis de proyectos legislativos de múltiples países (actualmente Colombia 🇨🇴 y Perú 🇵🇪).

---

## 🏗️ Arquitectura del Sistema

El proyecto sigue una arquitectura de **microservicios desacoplados**, separando la lógica de extracción (Scraping) de la orquestación (Airflow).

<img width="1678" height="732" alt="imagen" src="https://github.com/user-attachments/assets/ed12344e-7ff9-47f0-8fcf-34cdcb54eb97" />


### ¿Por qué separar Airflow del Scraper?

Esta decisión de diseño es intencional y ofrece ventajas críticas:

1.  **Desacoplamiento de Responsabilidades**:
    *   **Scraper API**: Se enfoca únicamente en *cómo* extraer los datos (selectores, navegadores, captchas, cambios en la web). Si la web del congreso cambia, solo se actualiza este servicio.
    *   **Airflow**: Se enfoca en *cuándo* y *qué* hacer con los datos (programación, reintentos, almacenamiento, alertas). No necesita saber de HTML o Selenium.

2.  **Escalabilidad Independiente**:
    *   El scraping (especialmente con Selenium) consume mucha RAM y CPU. Podemos escalar el servicio de scraping horizontalmente sin afectar al orquestador de Airflow.

3.  **Estabilidad**:
    *   Si un scraper falla o se cuelga (común en scraping), no tumba el servidor de Airflow. Airflow simplemente recibe un error y maneja el reintento.

4.  **Flexibilidad de Tecnologías**:
    *   El scraper service puede usar librerías específicas de Python para web (Selenium, Playwright, HTTPx) sin ensuciar el entorno de Airflow, que suele ser más restrictivo con las dependencias.

---

## 🚀 Inicio Rápido

Todo el sistema está contenerizado con Docker.

### Prerrequisitos
*   Docker & Docker Compose
*   Git

### Instalación

1.  **Clonar el repositorio**
    ```bash
    git clone <repo-url>
    cd scraper-project
    ```

2.  **Configurar variables de entorno**
    ```bash
    cp .env.example .env
    # Editar .env con tu API Key de Gemini si deseas clasificación automática
    ```

3.  **Iniciar servicios**
    ```bash
    cd docker
    docker-compose --env-file ../.env up -d
    ```

4.  **Acceder a las interfaces**
    *   **Airflow UI**: [http://localhost:8080](http://localhost:8080) (User/Pass: `airflow`)
    *   **Scraper API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **S3 (LocalStack)**: [http://localhost:4566](http://localhost:4566)

---

## 📦 Estructura del Proyecto

```
.
├── airflow/                 # Orquestador de tareas ETL
│   ├── dags/               # Definición de flujos de trabajo
│   ├── core/               # Lógica core reutilizable
│   └── helpers/            # Utilidades de extracción y carga
│
├── scraper-service/         # API REST de Scraping (FastAPI)
│   ├── app/
│   │   ├── dominios/       # Lógica específica por país (Colombia, Perú)
│   │   ├── scrapers/       # Motores base (Selenium, AJAX, HTTPx)
│   │   └── api/            # Endpoints REST
│
├── config/                  # Configuraciones JSON por país
├── docker/                  # Configuración de infraestructura Docker
└── data/                    # Volúmenes persistentes (ignorado en git)
```

---

## 🌍 Países Soportados

| País | Método | Velocidad | Características |
|------|--------|-----------|-----------------|
| 🇨🇴 **Colombia** | AJAX (Principal) | ⚡ Alta | Extracción API oculta, PDFs, Filtros avanzados |
| 🇨🇴 **Colombia** | Selenium (Backup)| 🐢 Baja | Navegación real, fallback robusto |
| 🇵🇪 **Perú** | HTTPx + BS4 | ⚡⚡ Ultra | Parsing HTML estático optimizado |

---

## 🛠️ Tecnologías Clave

*   **Python 3.11+**: Lenguaje base.
*   **FastAPI**: Framework para el servicio de scraping.
*   **Apache Airflow**: Orquestación de pipelines ETL.
*   **PostgreSQL**: Base de datos relacional principal.
*   **LocalStack (S3)**: Almacenamiento de objetos (Data Lake).
*   **Google Gemini AI**: Clasificación inteligente de proyectos por sector económico.
*   **Docker**: Contenerización completa.
