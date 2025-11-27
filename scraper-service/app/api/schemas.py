# schemas.py - Modelos Pydantic para la API

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


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


# ==================== ENUMS PARA FILTROS ====================

class TipoLeyEnum(str, Enum):
    """Tipos de ley disponibles"""
    ORDINARIA = "Ley Ordinaria"
    ORGANICA = "Ley Orgánica"
    ACTO_LEGISLATIVO = "Acto Legislativo"
    ESTATUTARIA = "Ley Estatutaria"


class EstadoLeyEnum(str, Enum):
    """Estados de ley disponibles"""
    TRAMITE_COMISION = "Trámite en Comisión"
    OTRO = "Otro"
    TRAMITE_PLENARIA = "Trámite en Plenaria"
    SANCION_PRESIDENCIAL = "Sanción Presidencial"
    PENDIENTE_PONENCIA_1 = "Pendiente ponencia primer debate"
    PENDIENTE_DESIGNAR = "Pendiente por designar ponentes"
    TRAMITE_CONCILIACION = "Trámite conciliación"
    DEBATE_COMISION = "Debate de Comisión"
    TRAMITE_SENADO = "Trámite en Senado"
    PENDIENTE_PONENCIA_2 = "Pendiente ponencia segundo debate"
    RETIRADO = "Retirado"
    LEY = "Ley"
    ARCHIVADO = "Archivado"
    ACTO_LEGISLATIVO_ESTADO = "Acto Legislativo"
    TRAMITE_OBJECIONES = "Trámite objeciones presidenciales"
    REVISION_CORTE = "Revisión corte constitucional"
    DEBATE_PLENARIA = "Debate de plenaria"
    SOLICITUD_AUDIENCIA = "Solicitud de Audiencia Pública"
    ACUMULADO = "Acumulado"
    DEBATE_SESION_CONJUNTA = "Debate de Sesión Conjunta"


class OrigenLeyEnum(str, Enum):
    """Origen de la ley"""
    CAMARA = "1"
    SENADO = "2"


class LegislaturaEnum(str, Enum):
    """Legislaturas disponibles"""
    L_2025_2026 = "2025-2026"
    L_2024_2025 = "2024-2025"
    L_2023_2024 = "2023-2024"
    L_2022_2023 = "2022-2023"
    L_2021_2022 = "2021-2022"
    L_2020_2021 = "2020-2021"
    L_2019_2020 = "2019-2020"
    L_2018_2019 = "2018-2019"
    L_2017_2018 = "2017-2018"
    L_2016_2017 = "2016-2017"
    L_2015_2016 = "2015-2016"
    L_2014_2015 = "2014-2015"


class ComisionEnum(str, Enum):
    """Comisiones constitucionales"""
    PRIMERA = "1"
    SEGUNDA = "2"
    TERCERA = "3"
    CUARTA = "4"
    QUINTA = "5"
    SEXTA = "6"
    SEPTIMA = "7"


class TipoScraperEnum(str, Enum):
    """Tipo de scraper a usar"""
    AJAX = "ajax"
    SELENIUM = "selenium"
