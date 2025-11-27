# routes.py - Rutas de la API

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from pathlib import Path

from .schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ProyectoResponse,
    HealthResponse
)
from ..utils.config_loader import config_loader
from ..utils.scraper_factory import scraper_factory

router = APIRouter()


@router.post("/scrape/{country}/{institution}", response_model=ScrapeResponse)
async def scrape_generic(
    country: str,
    institution: str,
    background_tasks: BackgroundTasks,
    legislatura: Optional[str] = Query(None, description="Filtrar por legislatura (ej: 2023-2024)"),
    max_pages: Optional[int] = Query(None, ge=1, description="Número máximo de páginas a scrapear"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio para el scraping (DD-MM-YYYY). Se detendrá al encontrar proyectos anteriores."),
    classify: bool = Query(True, description="Clasificar proyectos por sector económico con Gemini AI")
):
    """
    Ejecuta el scraping de proyectos de ley para cualquier país e institución configurada.
    
    - **country**: País a scrapear (ej: 'colombia', 'peru')
    - **institution**: Institución (ej: 'camara', 'senado', 'congreso')
    - **legislatura**: Filtro opcional por legislatura
    - **max_pages**: Límite de páginas a scrapear (útil para pruebas).
    - **fecha_inicio**: Fecha límite para el scraping (DD-MM-YYYY). Útil para cargas incrementales.
    - **classify**: Clasificar proyectos con Gemini AI (default: True)
    """
    try:
        # Cargar configuración
        config = config_loader.load(country)
        
        # Agregar límite de páginas a la configuración si se especificó
        if max_pages:
            config['limits'] = config.get('limits', {})
            config['limits']['max_pages'] = max_pages
        
        # Crear instancia del scraper usando el factory
        scraper = scraper_factory.create_by_country_institution(
            country=country,
            institution=institution,
            config=config,
            legislatura_filter=legislatura,
            fecha_inicio=fecha_inicio
        )
        
        # Ejecutar scraping
        resultados = await scraper.scrape()
        
        # Clasificar con Gemini AI si está habilitado
        if classify and resultados:
            try:
                from ..services.gemini_service import get_gemini_classifier
                
                classifier = get_gemini_classifier()
                resultados = await classifier.classify_batch(resultados)
                
            except Exception as e:
                # Si falla la clasificación, continuar sin ella
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Error en clasificación con Gemini: {str(e)}")
                logger.warning("Continuando sin clasificación...")
        
        pages_msg = f" ({max_pages} página{'s' if max_pages != 1 else ''})" if max_pages else ""
        date_msg = f" desde {fecha_inicio}" if fecha_inicio else ""
        classify_msg = " con clasificación AI" if classify and resultados else ""
        
        return ScrapeResponse(
            success=True,
            message=f"Scraping de {country.title()} - {institution.title()} completado{pages_msg}{date_msg}{classify_msg}. {len(resultados)} proyectos extraídos.",
            total_proyectos=len(resultados),
            proyectos=resultados
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el scraping: {str(e)}")


@router.post("/scrape/colombia", response_model=ScrapeResponse)
async def scrape_colombia(
    background_tasks: BackgroundTasks,
    legislatura: Optional[str] = Query(None, description="Filtrar por legislatura (ej: 2023-2024)"),
    max_pages: Optional[int] = Query(None, ge=1, le=617, description="Número máximo de páginas a scrapear (1-617)"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio para el scraping (DD-MM-YYYY). Se detendrá al encontrar proyectos anteriores."),
    classify: bool = Query(True, description="Clasificar proyectos por sector económico con Gemini AI")
):
    """
    Ejecuta el scraping de proyectos de ley de Colombia - Cámara de Representantes.
    
    **Endpoint de compatibilidad**: Use /scrape/colombia/camara para la nueva API genérica.
    
    - **legislatura**: Filtro opcional por legislatura
    - **max_pages**: Límite de páginas a scrapear (útil para pruebas).
    - **fecha_inicio**: Fecha límite para el scraping (DD-MM-YYYY). Útil para cargas incrementales.
    - **classify**: Clasificar proyectos con Gemini AI (default: True)
    """
    return await scrape_generic(
        country="colombia",
        institution="camara",
        background_tasks=background_tasks,
        legislatura=legislatura,
        max_pages=max_pages,
        fecha_inicio=fecha_inicio,
        classify=classify
    )


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
        config = config_loader.load(country)
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando configuración: {str(e)}")


@router.get("/scrapers/available")
async def list_available_scrapers():
    """
    Lista todos los scrapers disponibles y sus configuraciones.
    """
    try:
        scrapers = scraper_factory.list_available()
        configs = config_loader.list_available_configs()
        
        return {
            "scrapers": scrapers,
            "configurations": configs,
            "total_scrapers": len(scrapers),
            "total_configs": len(configs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando scrapers: {str(e)}")


@router.get("/gemini/sectores")
async def list_sectores_economicos():
    """
    Lista los sectores económicos disponibles para clasificación con Gemini.
    """
    try:
        from ..services.gemini_service import get_gemini_classifier
        
        classifier = get_gemini_classifier()
        sectores = classifier.get_sectores_disponibles()
        
        return {
            "sectores": sectores,
            "total": len(sectores),
            "modelo": "gemini-pro"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo sectores: {str(e)}")
