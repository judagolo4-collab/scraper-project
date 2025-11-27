#!/usr/bin/env python3
"""
Script de prueba para el scraper de Colombia.
Ejecuta el scraping de solo 1 página para verificar que todo funciona.
"""

import asyncio
import yaml
import sys
from pathlib import Path

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

from app.dominios.camara.colombia import CamaraColumbiaScraper


async def test_scraper():
    """Prueba el scraper con límite de 1 página"""
    
    # Cargar configuración
    config_path = Path(__file__).parent.parent / "config" / "colombia.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("=" * 80)
    print("🧪 PRUEBA DEL SCRAPER DE COLOMBIA - MODO LIMITADO (1 PÁGINA)")
    print("=" * 80)
    print(f"\n📋 Configuración cargada desde: {config_path}")
    print(f"🔗 URL: {config['url']}")
    print(f"🚗 ChromeDriver: {config['selenium']['driver_path']}")
    print(f"🌐 Chrome: {config['selenium']['chromium_path']}")
    print("\n" + "=" * 80)
    
    # Crear scraper
    scraper = CamaraColumbiaScraper(config)
    
    # Modificar temporalmente para solo 1 página
    original_next_page = scraper.next_page
    page_count = [0]  # Usar lista para poder modificar en closure
    
    async def limited_next_page(current_page):
        page_count[0] += 1
        if page_count[0] >= 1:  # Solo permitir 1 página
            print("\n⚠️  LÍMITE DE PRUEBA ALCANZADO (1 página)")
            return False
        return await original_next_page(current_page)
    
    scraper.next_page = limited_next_page
    
    try:
        # Ejecutar scraping
        print("\n🚀 Iniciando scraping de prueba...\n")
        resultados = await scraper.scrape()
        
        print("\n" + "=" * 80)
        print("✅ PRUEBA COMPLETADA")
        print("=" * 80)
        print(f"\n📊 Total de proyectos extraídos: {len(resultados)}")
        
        if resultados:
            print(f"\n📝 Ejemplo del primer proyecto:")
            print("-" * 80)
            primer_proyecto = resultados[0]
            for key, value in primer_proyecto.items():
                if value and len(str(value)) < 100:
                    print(f"  {key}: {value}")
                elif value:
                    print(f"  {key}: {str(value)[:97]}...")
            
            print("\n" + "=" * 80)
            print("🎯 CAMPOS CRÍTICOS VERIFICADOS:")
            print("=" * 80)
            
            checks = {
                "✅ Título extraído": bool(primer_proyecto.get('titulo')),
                "✅ Estado extraído": bool(primer_proyecto.get('estado')),
                "✅ URL de detalle": bool(primer_proyecto.get('url_detalle')),
                "✅ PDF encontrado": bool(primer_proyecto.get('url_pdf')),
                "✅ Fecha de radicación": bool(primer_proyecto.get('fecha_radicacion')),
                "✅ Resumen/Objeto": bool(primer_proyecto.get('resumen')),
            }
            
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check.replace('✅ ', '')}")
            
            all_passed = all(checks.values())
            
            print("\n" + "=" * 80)
            if all_passed:
                print("🎉 TODOS LOS CHECKS PASARON - EL SCRAPER ESTÁ FUNCIONANDO CORRECTAMENTE")
            else:
                print("⚠️  ALGUNOS CHECKS FALLARON - REVISAR SELECTORES")
            print("=" * 80)
            
        else:
            print("\n❌ No se extrajeron proyectos. Revisar selectores y configuración.")
        
        return resultados
        
    except Exception as e:
        print(f"\n❌ ERROR durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    resultados = asyncio.run(test_scraper())
    sys.exit(0 if resultados else 1)
