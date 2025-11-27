# routes.py - Rutas de la API

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
import yaml
import os
from pathlib import Path

from .schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ProyectoResponse,
    HealthResponse
)
from ..dominios.camara.colombia import CamaraColumbiaScraper

router = APIRouter()


def load_config(country: str) -> dict:
    """Carga la configuración desde el archivo YAML correspondiente"""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / f"{country.lower()}.yaml"
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"Configuración no encontrada para {country}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@router.post("/scrape/colombia", response_model=ScrapeResponse)
async def scrape_colombia(
    background_tasks: BackgroundTasks,
    legislatura: Optional[str] = Query(None, description="Filtrar por legislatura (ej: 2023-2024)"),
    max_pages: Optional[int] = Query(None, ge=1, le=617, description="Número máximo de páginas a scrapear (1-617)"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio para el scraping (DD-MM-YYYY). Se detendrá al encontrar proyectos anteriores.")
):
    """
    Ejecuta el scraping de proyectos de ley de Colombia - Cámara de Representantes.
    
    - **legislatura**: Filtro opcional por legislatura
    - **max_pages**: Límite de páginas a scrapear (útil para pruebas).
    - **fecha_inicio**: Fecha límite para el scraping (DD-MM-YYYY). Útil para cargas incrementales.
    """
    try:
        # Cargar configuración
        config = load_config("colombia")
        
        # Agregar límite de páginas a la configuración si se especificó
        if max_pages:
            config['limits'] = config.get('limits', {})
            config['limits']['max_pages'] = max_pages
        
        # Crear instancia del scraper
        scraper = CamaraColumbiaScraper(config, legislatura_filter=legislatura, fecha_inicio=fecha_inicio)
        
        # Ejecutar scraping
        resultados = await scraper.scrape()
        
        pages_msg = f" ({max_pages} página{'s' if max_pages != 1 else ''})" if max_pages else ""
        date_msg = f" desde {fecha_inicio}" if fecha_inicio else ""
        
        return ScrapeResponse(
            success=True,
            message=f"Scraping completado exitosamente{pages_msg}{date_msg}. {len(resultados)} proyectos extraídos.",
            total_proyectos=len(resultados),
            proyectos=resultados
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el scraping: {str(e)}")


@router.get("/scrape/colombia/status")
async def get_scrape_status():
    """
    Obtiene el estado del último scraping ejecutado.
    """
    return {
        "status": "not_implemented",
        "message": "Esta funcionalidad estará disponible en una versión futura"
    }


@router.get("/proyectos", response_model=List[ProyectoResponse])
async def list_proyectos(
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    legislatura: Optional[str] = Query(None, description="Filtrar por legislatura"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """
    Lista los proyectos almacenados en la base de datos.
    
    **Nota**: Esta funcionalidad requiere conexión a base de datos (próxima fase).
    """
    return []


@router.get("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
async def get_proyecto(proyecto_id: int):
    """
    Obtiene un proyecto específico por su ID.
    
    **Nota**: Esta funcionalidad requiere conexión a base de datos (próxima fase).
    """
    raise HTTPException(status_code=404, detail="Proyecto no encontrado")


@router.get("/config/{country}")
async def get_config(country: str):
    """
    Obtiene la configuración para un país específico.
    """
    try:
        config = load_config(country)
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando configuración: {str(e)}")
