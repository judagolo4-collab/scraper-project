#!/usr/bin/env python3
"""
Script para probar el endpoint de la API con un límite pequeño
"""

import requests
import json
import sys

def test_api_endpoint():
    """Prueba el endpoint de la API"""
    
    print("=" * 80)
    print("🧪 PRUEBA DEL ENDPOINT DE LA API")
    print("=" * 80)
    
    url = "http://localhost:8000/api/scrape/colombia/camara"
    
    # Parámetros query para limitar el scraping en tests
    params = {
        "max_pages": 1,
        "classify": False  # Sin clasificación de Gemini para test rápido
    }
    
    print(f"\n📡 Haciendo POST a: {url}")
    print(f"📋 Query params: {params}")
    print("⏳ Esto debería tomar ~30 segundos...\n")
    
    try:
        response = requests.post(url, params=params, timeout=120)  # 2 minutos de timeout
        response.raise_for_status()
        
        data = response.json()
        
        print("=" * 80)
        print("✅ RESPUESTA RECIBIDA")
        print("=" * 80)
        
        print(f"\nSuccess: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Total proyectos: {data.get('total_proyectos')}")
        
        if data.get('proyectos'):
            print(f"\n📝 Primer proyecto:")
            print(json.dumps(data['proyectos'][0], indent=2, ensure_ascii=False))
            
            # Guardar resultados
            with open('api_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Resultados guardados en: api_test_results.json")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: La petición tomó demasiado tiempo")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_api_endpoint()
    sys.exit(0 if success else 1)
