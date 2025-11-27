#!/usr/bin/env python3
"""
Script de prueba rápida para verificar que el scraper funciona correctamente
"""
import asyncio
import sys
import os

# Agregar el directorio padre al path para poder importar los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.config_loader import config_loader
from app.utils.scraper_factory import scraper_factory


async def test_scraper_quick():
    """Prueba rápida del scraper de Colombia"""
    print("🧪 Iniciando prueba del scraper de Colombia...")
    print("=" * 60)
    
    try:
        # 1. Verificar que se puede cargar la configuración
        print("\n📝 1. Cargando configuración...")
        config = config_loader.load('colombia')
        print(f"   ✅ Config cargada: {config.get('pais')} - {config.get('institucion')}")
        print(f"   ✅ URL: {config.get('url')}")
        
        # 2. Verificar que el scraper está registrado
        print("\n📝 2. Verificando scrapers disponibles...")
        available = scraper_factory.list_available()
        print(f"   ✅ Scrapers registrados: {available}")
        
        # 3. Crear instancia del scraper
        print("\n📝 3. Creando instancia del scraper...")
        config['limits']['max_pages'] = 1  # Solo 1 página para la prueba
        scraper = scraper_factory.create_by_country_institution(
            country='colombia',
            institution='camara',
            config=config
        )
        print(f"   ✅ Scraper creado: {scraper.__class__.__name__}")
        
        # 4. Ejecutar scraping (solo 1 página)
        print("\n📝 4. Ejecutando scraping (1 página)...")
        print("   ⏳ Esto puede tomar 30-60 segundos...")
        results = await scraper.scrape()
        
        # 5. Mostrar resultados
        print(f"\n✅ PRUEBA EXITOSA!")
        print("=" * 60)
        print(f"📊 Total de proyectos extraídos: {len(results)}")
        
        if results:
            print("\n📄 Primer proyecto extraído:")
            primer_proyecto = results[0]
            for key, value in primer_proyecto.items():
                if value:
                    # Truncar valores largos
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"   • {key}: {value_str}")
        
        print("\n" + "=" * 60)
        print("✨ ¡Todo funciona correctamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR durante la prueba:")
        print(f"   {str(e)}")
        import traceback
        print("\n🔍 Traceback completo:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n")
    print("=" * 60)
    print("   PRUEBA RÁPIDA DEL SISTEMA DE SCRAPING")
    print("=" * 60)
    
    success = asyncio.run(test_scraper_quick())
    
    sys.exit(0 if success else 1)

