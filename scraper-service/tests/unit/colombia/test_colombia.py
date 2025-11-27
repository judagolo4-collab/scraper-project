# test_colombia.py - Tests unitarios para el scraper de Colombia

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
from app.dominios.camara.colombia import CamaraColumbiaScraper


@pytest.fixture
def config():
    """Configuración de prueba"""
    return {
        "pais": "Colombia",
        "institucion": "Camara",
        "url": "https://www.camara.gov.co/secretaria/proyectos-de-ley#menu",
        "selenium": {
            "wait_time": 5,
            "driver_path": "/usr/bin/chromedriver"
        },
        "selectors": {
            "tabla_proyectos": "table tbody tr",
            "paginacion_siguiente": "button.pagina-btn[data-pagina='next']"
        },
        "pagination": {
            "next_button": "button.pagina-btn[data-pagina='next']",
            "click_delay": 1
        },
        "log_level": "DEBUG"
    }


@pytest.fixture
def scraper(config):
    """Instancia del scraper para pruebas"""
    return CamaraColumbiaScraper(config)


def test_scraper_initialization(scraper, config):
    """Test de inicialización del scraper"""
    assert scraper.url == config["url"]
    assert scraper.legislatura_filter is None
    assert scraper.selectors == config["selectors"]
    assert len(scraper.results) == 0


def test_scraper_with_legislatura_filter(config):
    """Test de scraper con filtro de legislatura"""
    scraper = CamaraColumbiaScraper(config, legislatura_filter="2023-2024")
    assert scraper.legislatura_filter == "2023-2024"


@pytest.mark.asyncio
async def test_extract_row_data(scraper):
    """Test de extracción de datos de una fila"""
    # Mock de una fila de tabla
    mock_row = Mock()
    mock_cells = []
    
    # Crear celdas mock
    cell_values = [
        "472",  # numero_camara
        "",     # numero_senado
        "LEY CATASTRO MULTIPROPÓSITO Ver detalle",  # proyecto
        "Ordinaria",  # tipo
        "Gobierno Nacional",  # autores
        "En trámite",  # estado
        "Cámara",  # origen
        "Tercera",  # comision
        "2024-2025"  # legislatura
    ]
    
    for value in cell_values:
        cell = Mock()
        cell.text.strip.return_value = value
        mock_cells.append(cell)
    
    # Mock del enlace en la celda del proyecto
    mock_link = Mock()
    mock_link.get_attribute.return_value = "https://www.camara.gov.co/ley-catastro-multiproposito/"
    mock_cells[2].find_element.return_value = mock_link
    
    mock_row.find_elements.return_value = mock_cells
    
    # Ejecutar extracción
    with patch.object(scraper, 'logger'):
        data = scraper._extract_row_data(mock_row)
    
    # Verificar datos extraídos
    assert data['numero_camara'] == "472"
    assert data['titulo'] == "LEY CATASTRO MULTIPROPÓSITO"
    assert data['tipo'] == "Ordinaria"
    assert data['estado'] == "En trámite"
    assert data['legislatura'] == "2024-2025"


def test_add_result(scraper):
    """Test de agregar resultado"""
    proyecto = {
        "titulo": "Test Proyecto",
        "numero_camara": "123"
    }
    
    scraper.add_result(proyecto)
    
    assert len(scraper.results) == 1
    assert scraper.results[0] == proyecto


def test_get_results(scraper):
    """Test de obtener resultados"""
    proyectos = [
        {"titulo": "Proyecto 1"},
        {"titulo": "Proyecto 2"}
    ]
    
    for p in proyectos:
        scraper.add_result(p)
    
    results = scraper.get_results()
    assert len(results) == 2
    assert results == proyectos


@pytest.mark.asyncio
async def test_scrape_with_mock_driver(scraper, config):
    """Test del método scrape con driver mockeado"""
    # Este test requiere mockear completamente el driver de Selenium
    # Por ahora, solo verificamos que el método existe y es async
    assert asyncio.iscoroutinefunction(scraper.scrape)
