#!/usr/bin/env python3
"""
Script para debuggear la extracción del resumen
"""

import asyncio
import yaml
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

async def debug_resumen():
    """Debug de la extracción del resumen"""
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.camara.gov.co/ley-catastro-multiproposito/"
        print(f"Navegando a: {url}")
        driver.get(url)
        time.sleep(3)
        
        print("\n" + "="*80)
        print("INTENTANDO DIFERENTES SELECTORES PARA EL RESUMEN")
        print("="*80)
        
        # Método 1: Buscar párrafo con Título
        try:
            elem = driver.find_element(By.XPATH,
                "//div[contains(@class, 'elementor-widget-text-editor')]//p[strong[contains(text(), 'Título')]]"
            )
            print(f"\n✅ Método 1 - Encontrado párrafo con 'Título'")
            print(f"Texto completo: {elem.text[:200]}...")
        except Exception as e:
            print(f"\n❌ Método 1 - Error: {e}")
        
        # Método 2: Buscar todo el div y analizar
        try:
            divs = driver.find_elements(By.CSS_SELECTOR, "div.elementor-widget-text-editor")
            print(f"\n✅ Método 2 - Encontrados {len(divs)} divs con clase elementor-widget-text-editor")
            for i, div in enumerate(divs[:3]):
                text = div.text[:150]
                print(f"  Div {i+1}: {text}...")
        except Exception as e:
            print(f"\n❌ Método 2 - Error: {e}")
        
        # Método 3: Buscar strong con Título y obtener el padre
        try:
            strong = driver.find_element(By.XPATH, "//strong[contains(text(), 'Título')]")
            parent = strong.find_element(By.XPATH, "..")
            print(f"\n✅ Método 3 - Encontrado strong 'Título'")
            print(f"Tag del padre: {parent.tag_name}")
            print(f"Texto del padre: {parent.text[:200]}...")
            
            # Obtener HTML interno
            html = driver.execute_script("return arguments[0].innerHTML;", parent)
            print(f"HTML del padre: {html[:300]}...")
        except Exception as e:
            print(f"\n❌ Método 3 - Error: {e}")
        
        # Método 4: Obtener todo el body y buscar manualmente
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if "Título" in body_text:
                lines = body_text.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith("Título"):
                        print(f"\n✅ Método 4 - Encontrado 'Título' en línea {i}")
                        print(f"Línea actual: {line}")
                        if i + 1 < len(lines):
                            print(f"Línea siguiente: {lines[i+1][:200]}...")
                        break
        except Exception as e:
            print(f"\n❌ Método 4 - Error: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(debug_resumen())
