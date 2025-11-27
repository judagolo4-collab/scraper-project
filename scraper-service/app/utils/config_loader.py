# config_loader.py - Cargador genérico de configuraciones

import json
import yaml  # type: ignore
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException


class ConfigLoader:
    """
    Clase para cargar configuraciones de scrapers desde archivos JSON o YAML.
    Busca automáticamente en el directorio de configuración.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa el cargador de configuración.
        
        :param config_dir: Directorio donde se encuentran los archivos de configuración.
                          Por defecto, busca en múltiples ubicaciones.
        """
        if config_dir is None:
            # Intentar múltiples ubicaciones para soporte de Docker y desarrollo local
            possible_dirs = [
                Path("/app/config"),  # Docker
                Path(__file__).parent.parent.parent.parent / "config",  # Desarrollo local
            ]
            
            self.config_dir: Optional[Path] = None
            for directory in possible_dirs:
                if directory.exists():
                    self.config_dir = directory
                    break
            
            if self.config_dir is None:
                raise FileNotFoundError(
                    f"Directorio de configuración no encontrado. Buscado en: {possible_dirs}"
                )
        else:
            self.config_dir = config_dir
            if not self.config_dir.exists():
                raise FileNotFoundError(f"Directorio de configuración no encontrado: {self.config_dir}")
    
    def load(self, country: str) -> Dict[str, Any]:
        """
        Carga la configuración para un país específico.
        Intenta primero con JSON, luego con YAML.
        
        :param country: Nombre del país (ej: 'colombia', 'peru')
        :return: Diccionario con la configuración
        """
        country = country.lower()
        
        # Intentar cargar JSON primero (preferido)
        json_path = self.config_dir / f"{country}.json"
        if json_path.exists():
            return self._load_json(json_path)
        
        # Si no existe JSON, intentar YAML
        yaml_path = self.config_dir / f"{country}.yaml"
        if yaml_path.exists():
            return self._load_yaml(yaml_path)
        
        # Si no se encuentra ninguno, lanzar error
        raise HTTPException(
            status_code=404,
            detail=f"Configuración no encontrada para '{country}'. Buscado en: {self.config_dir}"
        )
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Carga un archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error parseando JSON en {file_path}: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error leyendo archivo {file_path}: {str(e)}"
            )
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Carga un archivo YAML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error parseando YAML en {file_path}: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error leyendo archivo {file_path}: {str(e)}"
            )
    
    def list_available_configs(self) -> list[str]:
        """
        Lista todas las configuraciones disponibles.
        
        :return: Lista de nombres de países configurados
        """
        configs = []
        
        for file in self.config_dir.glob("*.json"):
            configs.append(file.stem)
        
        for file in self.config_dir.glob("*.yaml"):
            if file.stem not in configs:  # Evitar duplicados si existe JSON y YAML
                configs.append(file.stem)
        
        return sorted(configs)


# Instancia global del cargador
config_loader = ConfigLoader()

