#!/usr/bin/env python3
"""
Script para debuggear la extracción de la fecha
"""

import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import re

async def debug_fecha():
    """Debug de la extracción de fecha"""
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    
    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.camara.gov.co/ley-catastro-multiproposito/"
        print(f"Navegando a: {url}")
        driver.get(url)
        time.sleep(3)
        
        print("\n" + "="*80)
        print("ANALIZANDO FECHA DE RADICACIÓN")
        print("="*80)
        
        # Intento 1: Padre del strong
        try:
            elem = driver.find_element(By.XPATH, "//strong[contains(text(), 'Fecha de Radicación')]/parent::p")
            text = elem.text
            print(f"\n✅ Texto del contenedor (parent::p):")
            print(f"'{text}'")
            print(f"Longitud: {len(text)}")
            
            # Probar regex
            match = re.search(r'\d{2}/\d{2}/\d{4}', text)
            if match:
                print(f"✅ Regex encontró: {match.group(0)}")
            else:
                print(f"❌ Regex NO encontró fecha en formato DD/MM/YYYY")
                
        except Exception as e:
            print(f"❌ Error Intento 1: {e}")

        # Intento 2: Buscar cualquier fecha en el body cerca de "Fecha de Radicación"
        try:
            body = driver.find_element(By.TAG_NAME, "body").text
            idx = body.find("Fecha de Radicación")
            if idx != -1:
                context = body[idx:idx+200]
                print(f"\n✅ Contexto en body (200 chars):")
                print(f"'{context}'")
        except:
            pass
            
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(debug_fecha())
