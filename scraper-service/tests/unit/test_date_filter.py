#!/usr/bin/env python3
"""
Script para probar el filtrado por fecha
"""

import requests
import json
import sys
from datetime import datetime

def test_date_filter():
    """Prueba el endpoint con filtro de fecha"""
    
    print("=" * 80)
    print("🧪 PRUEBA DE FILTRADO POR FECHA")
    print("=" * 80)
    
    # Usamos una fecha reciente para que se detenga rápido
    # Nota: Depende de los datos reales en la web. 
    # Si el proyecto más reciente es del 18/11/2025, usaremos 01/11/2025
    fecha_inicio = "01-11-2025"
    
    url = f"http://localhost:8000/api/scrape/colombia?fecha_inicio={fecha_inicio}&max_pages=2"
    
    print(f"\n📡 Haciendo POST a: {url}")
    print(f"📅 Fecha límite: {fecha_inicio}")
    
    try:
        response = requests.post(url, timeout=300)
        response.raise_for_status()
        
        data = response.json()
        
        print("=" * 80)
        print("✅ RESPUESTA RECIBIDA")
        print("=" * 80)
        
        print(f"Total proyectos: {data.get('total_proyectos')}")
        
        proyectos = data.get('proyectos', [])
        
        # Verificar fechas
        fechas_ok = True
        for p in proyectos:
            fecha_str = p.get('fecha_radicacion')
            if fecha_str:
                try:
                    fecha_p = datetime.strptime(fecha_str, '%d/%m/%Y')
                    fecha_limite = datetime.strptime(fecha_inicio, '%d-%m-%Y')
                    
                    if fecha_p < fecha_limite:
                        print(f"❌ ERROR: Proyecto con fecha {fecha_str} es anterior al límite {fecha_inicio}")
                        fechas_ok = False
                    else:
                        print(f"✅ OK: {fecha_str} >= {fecha_inicio}")
                except:
                    print(f"⚠️ No se pudo parsear fecha: {fecha_str}")
        
        if fechas_ok:
            print("\n🎉 FILTRADO EXITOSO: Todos los proyectos cumplen el criterio de fecha.")
        else:
            print("\n❌ FALLO EN FILTRADO: Se encontraron proyectos fuera de rango.")
            
        return fechas_ok
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_date_filter()
    sys.exit(0 if success else 1)
