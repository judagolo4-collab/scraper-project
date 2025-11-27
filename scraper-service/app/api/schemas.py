# schemas.py - Modelos Pydantic para la API

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


class ScrapeRequest(BaseModel):
    """Request para iniciar un scraping"""
    pais: str = Field(..., description="País a scrapear (colombia, peru, etc.)")
    institucion: str = Field(..., description="Institución (camara, senado)")
    legislatura: Optional[str] = Field(None, description="Filtro por legislatura")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pais": "colombia",
                "institucion": "camara",
                "legislatura": "2023-2024"
            }
        }


class ProyectoResponse(BaseModel):
    """Respuesta con datos de un proyecto"""
    # Datos básicos
    numero_camara: Optional[str] = None
    numero_senado: Optional[str] = None
    titulo: str
    tipo: Optional[str] = None
    autores: Optional[str] = None
    estado: Optional[str] = None
    origen: Optional[str] = None
    comision: Optional[str] = None
    legislatura: Optional[str] = None
    
    # Datos de detalle
    fecha_radicacion: Optional[str] = None
    resumen: Optional[str] = None
    url_detalle: Optional[str] = None
    url_pdf: Optional[str] = None
    url_gaceta: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "numero_camara": "472",
                "numero_senado": "",
                "titulo": "LEY CATASTRO MULTIPROPÓSITO",
                "tipo": "Ordinaria",
                "autores": "Gobierno Nacional",
                "estado": "En trámite",
                "origen": "Cámara",
                "comision": "Tercera",
                "legislatura": "2024-2025",
                "fecha_radicacion": "2025-11-20",
                "resumen": "Por medio de la cual se establece...",
                "url_pdf": "https://www.camara.gov.co/wp-content/uploads/...",
                "url_gaceta": "https://..."
            }
        }


class ScrapeResponse(BaseModel):
    """Respuesta del endpoint de scraping"""
    success: bool
    message: str
    total_proyectos: int
    proyectos: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Scraping completado exitosamente",
                "total_proyectos": 150,
                "proyectos": []
            }
        }


class HealthResponse(BaseModel):
    """Respuesta del health check"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
