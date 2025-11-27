# gemini_service.py - Servicio para clasificar proyectos con Gemini AI

import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiClassifier:
    """
    Servicio para clasificar proyectos de ley por sectores económicos
    usando la API de Gemini.
    """
    
    # Sectores económicos predefinidos
    SECTORES_ECONOMICOS = [
        "Minero-Energético",
        "Agricultura y Desarrollo Rural",
        "Tecnología y Telecomunicaciones",
        "Servicios Financieros",
        "Salud y Seguridad Social",
        "Educación",
        "Transporte e Infraestructura",
        "Comercio e Industria",
        "Turismo y Cultura",
        "Medio Ambiente",
        "Justicia y Seguridad",
        "Laboral y Empleo",
        "Tributario y Fiscal",
        "Vivienda y Desarrollo Urbano",
        "Defensa y Fuerzas Armadas",
        "Relaciones Exteriores",
        "Ciencia y Tecnología",
        "Deportes y Recreación",
        "Social y Bienestar",
        "Administrativo y Gubernamental",
        "Otros"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el clasificador de Gemini.
        
        :param api_key: Clave de API de Gemini (si no se proporciona, lee de .env)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY no encontrada. "
                "Configúrala en el archivo .env o pásala como parámetro."
            )
        
        self.base_url = "https://generativelanguage.googleapis.com/v1"
        self.model = "gemini-2.0-flash"  # Modelo Gemini 2.0 Flash (disponible)
        self.endpoint = f"{self.base_url}/models/{self.model}:generateContent"
        
        logger.info("✅ GeminiClassifier inicializado correctamente")
    
    def _build_prompt(self, proyectos: List[Dict[str, Any]]) -> str:
        """
        Construye el prompt para Gemini con todos los proyectos.
        """
        sectores_str = ", ".join(self.SECTORES_ECONOMICOS)
        
        prompt = f"""Eres un experto en legislación y economía. Tu tarea es clasificar proyectos de ley colombianos por sector económico.

SECTORES DISPONIBLES:
{sectores_str}

INSTRUCCIONES:
1. Analiza el título y resumen de cada proyecto
2. Asigna el sector económico más apropiado
3. Si no encaja claramente en ninguno, usa "Otros"
4. Responde SOLO con un JSON válido (sin markdown, sin ```json)

FORMATO DE RESPUESTA (JSON válido):
[
  {{"numero_camara": "472/2025C", "sector_economico": "Tributario y Fiscal"}},
  {{"numero_camara": "473/2025C", "sector_economico": "Salud y Seguridad Social"}}
]

PROYECTOS A CLASIFICAR:
"""
        
        # Agregar proyectos
        for i, proyecto in enumerate(proyectos, 1):
            titulo = proyecto.get('titulo', 'N/A')
            resumen = proyecto.get('resumen', 'N/A')
            numero = proyecto.get('numero_camara', 'N/A')
            tipo = proyecto.get('tipo', 'N/A')
            
            # Truncar resumen si es muy largo
            if resumen and len(resumen) > 200:
                resumen = resumen[:200] + "..."
            
            prompt += f"\n{i}. Número: {numero}\n"
            prompt += f"   Tipo: {tipo}\n"
            prompt += f"   Título: {titulo}\n"
            prompt += f"   Resumen: {resumen}\n"
        
        prompt += "\nRespuesta (JSON válido sin markdown):"
        
        return prompt
    
    async def classify_batch(
        self,
        proyectos: List[Dict[str, Any]],
        batch_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Clasifica múltiples proyectos por lotes.
        
        :param proyectos: Lista de proyectos a clasificar
        :param batch_size: Tamaño del lote (Gemini tiene límites de tokens)
        :return: Lista de proyectos con sector_economico agregado
        """
        if not proyectos:
            logger.warning("No hay proyectos para clasificar")
            return []
        
        logger.info(f"🤖 Clasificando {len(proyectos)} proyectos con Gemini AI...")
        logger.info(f"📦 Procesando en lotes de {batch_size} proyectos")
        
        clasificados = []
        total_batches = (len(proyectos) + batch_size - 1) // batch_size
        
        # Procesar por lotes
        for i in range(0, len(proyectos), batch_size):
            batch = proyectos[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"📊 Procesando lote {batch_num}/{total_batches} ({len(batch)} proyectos)")
            
            try:
                # Clasificar el lote
                clasificaciones = await self._classify_single_batch(batch)
                
                # Crear diccionario de clasificaciones
                clasificaciones_dict = {
                    c['numero_camara']: c['sector_economico']
                    for c in clasificaciones
                }
                
                # Agregar sector a cada proyecto
                for proyecto in batch:
                    numero = proyecto.get('numero_camara', '')
                    sector = clasificaciones_dict.get(numero, 'Sin clasificar')
                    
                    proyecto_clasificado = proyecto.copy()
                    proyecto_clasificado['sector_economico'] = sector
                    clasificados.append(proyecto_clasificado)
                
                logger.info(f"✅ Lote {batch_num}/{total_batches} clasificado correctamente")
                
            except Exception as e:
                logger.error(f"❌ Error clasificando lote {batch_num}: {str(e)}")
                
                # Agregar sin clasificar en caso de error
                for proyecto in batch:
                    proyecto_clasificado = proyecto.copy()
                    proyecto_clasificado['sector_economico'] = 'Error en clasificación'
                    clasificados.append(proyecto_clasificado)
        
        logger.info(f"✨ Clasificación completada: {len(clasificados)} proyectos")
        return clasificados
    
    async def _classify_single_batch(self, proyectos: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Clasifica un solo lote de proyectos.
        
        :return: Lista de dicts con {numero_camara, sector_economico}
        """
        prompt = self._build_prompt(proyectos)
        
        # Preparar request para Gemini
        request_body = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,  # Baja temperatura para respuestas más consistentes
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        # Llamar a la API de Gemini
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.endpoint}?key={self.api_key}",
                json=request_body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"Error en API de Gemini: {error_msg}")
                raise Exception(f"Error en Gemini API: {response.status_code} - {error_msg}")
            
            result = response.json()
        
        # Extraer texto de la respuesta
        try:
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # Limpiar respuesta (remover markdown si existe)
            text_response = text_response.strip()
            if text_response.startswith('```json'):
                text_response = text_response[7:]
            if text_response.startswith('```'):
                text_response = text_response[3:]
            if text_response.endswith('```'):
                text_response = text_response[:-3]
            text_response = text_response.strip()
            
            # Parsear JSON
            clasificaciones = json.loads(text_response)
            
            logger.debug(f"Clasificaciones recibidas: {len(clasificaciones)}")
            return clasificaciones
            
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error parseando respuesta de Gemini: {str(e)}")
            logger.debug(f"Respuesta completa: {result}")
            
            # Retornar clasificaciones por defecto
            return [
                {
                    'numero_camara': p.get('numero_camara', ''),
                    'sector_economico': 'Error en clasificación'
                }
                for p in proyectos
            ]
    
    def get_sectores_disponibles(self) -> List[str]:
        """Retorna la lista de sectores económicos disponibles"""
        return self.SECTORES_ECONOMICOS.copy()


# Instancia global (singleton)
_gemini_classifier: Optional[GeminiClassifier] = None


def get_gemini_classifier() -> GeminiClassifier:
    """
    Obtiene la instancia singleton del clasificador de Gemini.
    """
    global _gemini_classifier
    
    if _gemini_classifier is None:
        _gemini_classifier = GeminiClassifier()
    
    return _gemini_classifier

