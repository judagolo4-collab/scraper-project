#!/usr/bin/env python3
"""
Script de prueba rápida para el scraper de Perú
"""

import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_peru_scraper():
    url = "https://www2.congreso.gob.pe/Sicr/TraDocEstProc/CLProLey2011.nsf/Local%20Por%20Numero%20Inverso?OpenView"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"🌐 Fetching: {url}")
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        html = response.text
    
    print(f"📄 HTML length: {len(html)} bytes")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Buscar todas las tablas
    tables = soup.find_all('table')
    print(f"\n📊 Total de tablas encontradas: {len(tables)}")
    
    for i, table in enumerate(tables):
        print(f"\nTabla {i+1}:")
        print(f"  - Atributos: {table.attrs}")
        rows = table.find_all('tr')
        print(f"  - Total de filas: {len(rows)}")
        
        # Buscar filas con valign="top"
        data_rows = table.find_all('tr', valign='top')
        print(f"  - Filas de datos (valign='top'): {len(data_rows)}")
        
        if data_rows:
            print(f"\n  📄 Primera fila de datos:")
            first_row = data_rows[0]
            cells = first_row.find_all('td')
            print(f"    - Total de celdas: {len(cells)}")
            
            for j, cell in enumerate(cells[:5]):  # Mostrar solo las primeras 5
                text = cell.get_text(strip=True)[:100]
                print(f"    - Celda {j+1}: {text}...")

if __name__ == "__main__":
    asyncio.run(test_peru_scraper())

