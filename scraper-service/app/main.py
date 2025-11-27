# main.py - Entry point de la aplicación FastAPI

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .api import routes

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando aplicación de scraping...")
    yield
    logger.info("🛑 Cerrando aplicación...")


# Crear instancia de FastAPI
app = FastAPI(
    title="Scraper de Proyectos de Ley",
    description="API para scraping de proyectos de ley de Colombia y otros países",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "🔍 Scraping",
            "description": "Endpoints para ejecutar scraping de proyectos de ley"
        },
        {
            "name": "🤖 Gemini AI",
            "description": "Endpoints relacionados con clasificación mediante Gemini AI"
        }
    ]
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas con categorías
app.include_router(routes.scraping_router, prefix="/api")
app.include_router(routes.gemini_router, prefix="/api")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "API de Scraping de Proyectos de Ley",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
