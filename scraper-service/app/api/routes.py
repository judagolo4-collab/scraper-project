# routes.py - Rutas de la API

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from pathlib import Path
import logging

from .schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ProyectoResponse,
    HealthResponse,
    TipoLeyEnum,
    EstadoLeyEnum,
    OrigenLeyEnum,
    LegislaturaEnum,
    ComisionEnum,
    TipoScraperEnum
)
from ..utils.config_loader import config_loader
from ..utils.scraper_factory import scraper_factory

logger = logging.getLogger(__name__)

# Routers con categorías
scraping_router = APIRouter(prefix="/scrape", tags=["🔍 Scraping"])
gemini_router = APIRouter(prefix="/gemini", tags=["🤖 Gemini AI"])


@scraping_router.post("/{country}", response_model=ScrapeResponse)
async def scrape_country(
    country: str,
    background_tasks: BackgroundTasks,
    tipo_scraper: TipoScraperEnum = Query(TipoScraperEnum.AJAX, description="🔧 Tipo de scraper"),
    legislatura: Optional[LegislaturaEnum] = Query(None, description="📅 Legislatura"),
    max_pages: Optional[int] = Query(None, ge=1, le=100, description="📄 Páginas (1-100)"),
    classify: bool = Query(True, description="🤖 Clasificar con Gemini AI"),
    tipo: Optional[TipoLeyEnum] = Query(None, description="📋 Tipo de ley"),
    estado: Optional[EstadoLeyEnum] = Query(None, description="📊 Estado"),
    origen: Optional[OrigenLeyEnum] = Query(None, description="🏛️ Origen"),
    comision: Optional[ComisionEnum] = Query(None, description="👥 Comisión")
):
    """
    🇨🇴 Scraping de proyectos de ley de Colombia.
    
    **Tipo de scraper:**
    - **ajax**: ⚡ Rápido (10-50x más rápido, recomendado)
    - **selenium**: 🐢 Completo pero lento
    
    **Filtros disponibles:**
    - Legislatura, Tipo, Estado, Origen, Comisión
    
    **Nota:** Los filtros solo funcionan con tipo_scraper="ajax"
    """
    try:
        # Cargar configuración
        config = config_loader.load(country)
        
        # Agregar límite de páginas a la configuración si se especificó
        if max_pages:
            config['limits'] = config.get('limits', {})
            config['limits']['max_pages'] = max_pages
        
        # Crear instancia del scraper usando el factory
        use_ajax = (tipo_scraper == TipoScraperEnum.AJAX)
        
        # Preparar kwargs según el país
        kwargs = {'max_pages': max_pages}
        
        # Parámetros específicos por país
        if country.lower() == 'colombia':
            kwargs.update({
                'legislatura_filter': legislatura.value if legislatura else None,
                'tipo_filter': tipo.value if tipo else None,
                'estado_filter': estado.value if estado else None,
                'origen_filter': origen.value if origen else None,
                'comision_filter': comision.value if comision else None,
            })
        elif country.lower() == 'peru':
            # Perú usa diferentes parámetros
            kwargs.update({
                'periodo_filter': legislatura.value if legislatura else None,
            })
        
        scraper = scraper_factory.create_by_country(
            country=country,
            config=config,
            use_ajax=use_ajax,
            **kwargs
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
                logger.warning(f"⚠️ Error en clasificación con Gemini: {str(e)}")
                logger.warning("Continuando sin clasificación...")
        
        pages_msg = f" ({max_pages} página{'s' if max_pages != 1 else ''})" if max_pages else ""
        classify_msg = " con clasificación AI" if classify and resultados else ""
        method_msg = f" ({tipo_scraper.value.upper()})"
        
        return ScrapeResponse(
            success=True,
            message=f"Scraping de {country.title()} completado{pages_msg}{classify_msg}{method_msg}. {len(resultados)} proyectos extraídos.",
            total_proyectos=len(resultados),
            proyectos=resultados
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el scraping: {str(e)}")






@gemini_router.get("/sectores")
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
