.PHONY: help setup install run test clean docker-up docker-down

help:  ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Configurar el entorno inicial
	@echo "🔧 Configurando entorno..."
	cd scraper-service && python -m venv venv
	@echo "✅ Entorno virtual creado"
	@echo "💡 Activa el entorno con: source scraper-service/venv/bin/activate"

install:  ## Instalar dependencias
	@echo "📦 Instalando dependencias..."
	cd scraper-service && pip install -r requirements.txt
	@echo "✅ Dependencias instaladas"

run:  ## Ejecutar el servicio localmente
	@echo "🚀 Iniciando servicio..."
	cd scraper-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Ejecutar tests
	@echo "🧪 Ejecutando tests..."
	cd scraper-service && pytest tests/ -v

test-cov:  ## Ejecutar tests con cobertura
	@echo "🧪 Ejecutando tests con cobertura..."
	cd scraper-service && pytest tests/ --cov=app --cov-report=html --cov-report=term

clean:  ## Limpiar archivos temporales
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Limpieza completada"

docker-build:  ## Construir imágenes Docker
	@echo "🏗️ Construyendo imágenes Docker..."
	cd docker && docker-compose build
	@echo "✅ Imágenes construidas"

docker-up:  ## Levantar servicios con Docker Compose
	@echo "🐳 Levantando servicios con Docker..."
	cd docker && docker-compose up -d
	@echo "✅ Servicios levantados"
	@echo "📡 API disponible en: http://localhost:8000"
	@echo "📊 PgAdmin disponible en: http://localhost:5050"

docker-down:  ## Detener servicios Docker
	@echo "🛑 Deteniendo servicios Docker..."
	cd docker && docker-compose down
	@echo "✅ Servicios detenidos"

docker-logs:  ## Ver logs de Docker
	cd docker && docker-compose logs -f

docker-restart:  ## Reiniciar servicios Docker
	@echo "🔄 Reiniciando servicios..."
	cd docker && docker-compose restart
	@echo "✅ Servicios reiniciados"

scrape-colombia:  ## Ejecutar scraping de Colombia (requiere servicio activo)
	@echo "🕷️ Ejecutando scraping de Colombia..."
	curl -X POST "http://localhost:8000/api/scrape/colombia" -H "Content-Type: application/json"

lint:  ## Ejecutar linter
	@echo "🔍 Ejecutando linter..."
	cd scraper-service && flake8 app/ --max-line-length=120

format:  ## Formatear código con black
	@echo "✨ Formateando código..."
	cd scraper-service && black app/ tests/
