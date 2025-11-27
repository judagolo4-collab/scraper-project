# colombia_filters.py - Mapeos de filtros para la API de Colombia

"""
Diccionarios de mapeo para los filtros de la API AJAX de la Cámara de Representantes.
Estos valores se obtuvieron inspeccionando la web y el endpoint admin-ajax.php
"""

# Tipos de Ley
TIPO_LEY = {
    "All": "Todos",
    "1": "Ley Ordinaria",
    "2": "Ley Orgánica",
    "3": "Acto Legislativo",
    "4": "Ley Estatutaria"
}

# Estados de Ley
ESTADO_LEY = {
    "All": "Todos",
    "1": "Trámite en Comisión",
    "2": "Otro",
    "3": "Trámite en Plenaria",
    "4": "Sanción Presidencial",
    "5": "Pendiente ponencia primer debate",
    "6": "Pendiente por designar ponentes",
    "7": "Trámite conciliación",
    "8": "Debate de Comisión",
    "9": "Trámite en Senado",
    "10": "Pendiente ponencia segundo debate",
    "11": "Retirado",
    "12": "Ley",
    "13": "Archivado",
    "14": "Acto Legislativo",
    "15": "Trámite objeciones presidenciales",
    "16": "Revisión corte constitucional",
    "17": "Debate de plenaria",
    "18": "Solicitud de Audiencia Pública",
    "21": "Acumulado",
    "22": "Debate de Sesión Conjunta"
}

# Origen de la Ley
ORIGEN_LEY = {
    "All": "Todos",
    "1": "Cámara",
    "2": "Senado"
}

# Legislaturas
LEGISLATURA = {
    "All": "Todas",
    "13": "2025-2026",
    "3": "2024-2025",
    "2": "2023-2024",
    "1": "2022-2023",
    "5": "2021-2022",
    "6": "2020-2021",
    "7": "2019-2020",
    "8": "2018-2019",
    "9": "2017-2018",
    "10": "2016-2017",
    "11": "2015-2016",
    "12": "2014-2015"
}

# Comisiones
COMISION = {
    "All": "Todas",
    "1": "Comisión Primera Constitucional Permanente",
    "2": "Comisión Segunda Constitucional Permanente",
    "3": "Comisión Tercera Constitucional Permanente",
    "4": "Comisión Cuarta Constitucional Permanente",
    "5": "Comisión Quinta Constitucional Permanente",
    "6": "Comisión Sexta Constitucional Permanente",
    "7": "Comisión Séptima Constitucional Permanente",
    "8": "Comisiones Legales",
    "9": "Comisión Accidental Conjunta",
    "10": "Comisión de Ética y Estatuto del Congresista",
    "11": "Comisión Legal de Cuentas",
    "12": "Comisión de Derechos Humanos y Audiencias"
}


def get_legislatura_id(legislatura_name: str) -> str:
    """
    Convierte un nombre de legislatura (ej: "2024-2025") a su ID.
    
    Args:
        legislatura_name: Nombre de la legislatura (ej: "2024-2025")
        
    Returns:
        ID de la legislatura o "All" si no se encuentra
    """
    for key, value in LEGISLATURA.items():
        if value == legislatura_name:
            return key
    return "All"


def get_tipo_ley_id(tipo_name: str) -> str:
    """
    Convierte un nombre de tipo de ley a su ID.
    
    Args:
        tipo_name: Nombre del tipo (ej: "Ley Ordinaria")
        
    Returns:
        ID del tipo o "All" si no se encuentra
    """
    for key, value in TIPO_LEY.items():
        if value.lower() == tipo_name.lower():
            return key
    return "All"


def get_estado_ley_id(estado_name: str) -> str:
    """
    Convierte un nombre de estado a su ID.
    
    Args:
        estado_name: Nombre del estado (ej: "Trámite en Comisión")
        
    Returns:
        ID del estado o "All" si no se encuentra
    """
    for key, value in ESTADO_LEY.items():
        if value.lower() == estado_name.lower():
            return key
    return "All"

