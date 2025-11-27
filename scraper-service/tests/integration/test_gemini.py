#!/usr/bin/env python3
"""
Script de prueba de integración con Gemini AI
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.gemini_service import get_gemini_classifier


async def test_gemini_classification():
    """Prueba la clasificación con Gemini"""
    print("🤖 Probando integración con Gemini AI...")
    print("=" * 60)
    
    # Proyectos de prueba
    proyectos_prueba = [
        {
            "numero_camara": "001/2024C",
            "titulo": "LEY DE ENERGÍAS RENOVABLES",
            "resumen": "Por la cual se promueve el uso de energía solar, eólica y otras fuentes renovables en Colombia",
            "tipo": "Ley Ordinaria"
        },
        {
            "numero_camara": "002/2024C",
            "titulo": "REFORMA TRIBUTARIA",
            "resumen": "Por medio de la cual se modifica el impuesto sobre la renta y se establecen nuevos tributos",
            "tipo": "Ley Ordinaria"
        },
        {
            "numero_camara": "003/2024C",
            "titulo": "LEY DE TELEMEDICINA",
            "resumen": "Por la cual se regula la prestación de servicios de salud a través de medios tecnológicos",
            "tipo": "Ley Ordinaria"
        },
        {
            "numero_camara": "004/2024C",
            "titulo": "LEY DE AGRICULTURA SOSTENIBLE",
            "resumen": "Por medio de la cual se promueve la agricultura orgánica y el desarrollo rural sostenible",
            "tipo": "Ley Ordinaria"
        },
        {
            "numero_camara": "005/2024C",
            "titulo": "LEY DE CIBERSEGURIDAD",
            "resumen": "Por la cual se establecen normas para la protección de datos y seguridad informática",
            "tipo": "Ley Ordinaria"
        }
    ]
    
    try:
        # 1. Obtener el clasificador
        print("\n📝 1. Inicializando clasificador...")
        classifier = get_gemini_classifier()
        print("   ✅ Clasificador inicializado correctamente")
        
        # 2. Ver sectores disponibles
        print("\n📝 2. Sectores económicos disponibles:")
        sectores = classifier.get_sectores_disponibles()
        print(f"   ✅ Total: {len(sectores)} sectores")
        for i, sector in enumerate(sectores[:5], 1):
            print(f"      {i}. {sector}")
        print(f"      ... y {len(sectores) - 5} más")
        
        # 3. Clasificar proyectos
        print(f"\n📝 3. Clasificando {len(proyectos_prueba)} proyectos de prueba...")
        print("   ⏳ Esto puede tomar 5-10 segundos...")
        
        resultados = await classifier.classify_batch(proyectos_prueba, batch_size=5)
        
        # 4. Mostrar resultados
        print("\n✅ CLASIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("\n📊 Resultados:\n")
        
        for i, proyecto in enumerate(resultados, 1):
            print(f"{i}. {proyecto['numero_camara']}")
            print(f"   Título: {proyecto['titulo']}")
            print(f"   Sector: 🎯 {proyecto['sector_economico']}")
            print()
        
        # 5. Resumen
        print("=" * 60)
        print(f"✨ {len(resultados)} proyectos clasificados correctamente")
        print("\n🎉 ¡Integración con Gemini AI funciona perfectamente!")
        
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
    print("   PRUEBA DE INTEGRACIÓN CON GEMINI AI")
    print("=" * 60)
    
    success = asyncio.run(test_gemini_classification())
    
    sys.exit(0 if success else 1)

