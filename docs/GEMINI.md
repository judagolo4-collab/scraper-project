# 🤖 INTEGRACIÓN GEMINI AI - Guía Completa

## ✅ ¿Qué se Implementó?

### 1. 🤖 Clasificación Automática por Sectores Económicos
- **Servicio**: `app/services/gemini_service.py`
- **Modelo**: Gemini Pro de Google
- **Método**: Clasificación en batch (eficiente y económico)

### 2. 🎭 User-Agents Rotativos
- **Archivo**: `app/scrapers/user_agents.py`
- **Beneficio**: Evita detección y bloqueos
- **Variedad**: 15+ user agents diferentes

### 3. 🔒 Variables de Entorno
- **Archivo**: `.env` (tu clave API segura)
- **Formato**: Clave no hardcodeada en el código

---

## 🎯 Sectores Económicos Disponibles

El sistema clasifica automáticamente en 21 sectores:

```
1.  Minero-Energético
2.  Agricultura y Desarrollo Rural
3.  Tecnología y Telecomunicaciones
4.  Servicios Financieros
5.  Salud y Seguridad Social
6.  Educación
7.  Transporte e Infraestructura
8.  Comercio e Industria
9.  Turismo y Cultura
10. Medio Ambiente
11. Justicia y Seguridad
12. Laboral y Empleo
13. Tributario y Fiscal
14. Vivienda y Desarrollo Urbano
15. Defensa y Fuerzas Armadas
16. Relaciones Exteriores
17. Ciencia y Tecnología
18. Deportes y Recreación
19. Social y Bienestar
20. Administrativo y Gubernamental
21. Otros
```

---

## 🚀 Cómo Usar

### 1. Configurar la Clave API

Tu clave ya está configurada en `.env`:

```bash
GEMINI_API_KEY=AIzaSyAjFBkDoLwGL7DPNO_Z7rSW1fK6IhX3jxY
```

⚠️ **IMPORTANTE**: NO subir `.env` a git (ya está en `.gitignore`)

### 2. Instalar Dependencias

```bash
cd scraper-service
source venv/bin/activate
pip install python-dotenv httpx
```

### 3. Usar el Scraper con Clasificación

```bash
# CON clasificación Gemini (por defecto)
curl -X POST "http://localhost:8000/api/scrape/colombia?max_pages=1"

# SIN clasificación Gemini
curl -X POST "http://localhost:8000/api/scrape/colombia?max_pages=1&classify=false"
```

---

## 📊 Ejemplo de Respuesta

### Antes (sin Gemini):
```json
{
  "numero_camara": "472/2025C",
  "titulo": "LEY CATASTRO MULTIPROPÓSITO ()",
  "tipo": "Ley Ordinaria",
  "estado": "Trámite en Comisión",
  "resumen": "Por medio de la cual se fortalece..."
}
```

### Ahora (con Gemini):
```json
{
  "numero_camara": "472/2025C",
  "titulo": "LEY CATASTRO MULTIPROPÓSITO ()",
  "tipo": "Ley Ordinaria",
  "estado": "Trámite en Comisión",
  "resumen": "Por medio de la cual se fortalece...",
  "sector_economico": "Tributario y Fiscal"  ← ✨ NUEVO
}
```

---

## 🎯 Endpoints Nuevos

### 1. Ver Sectores Disponibles

```bash
GET /api/gemini/sectores

# Respuesta:
{
  "sectores": [
    "Minero-Energético",
    "Agricultura y Desarrollo Rural",
    ...
  ],
  "total": 21,
  "modelo": "gemini-pro"
}
```

### 2. Scraping con/sin Clasificación

```bash
# Con clasificación (default)
POST /api/scrape/colombia?max_pages=1

# Sin clasificación
POST /api/scrape/colombia?max_pages=1&classify=false
```

---

## ⚙️ Configuración del Servicio

### Clasificación en Batch

El sistema clasifica **en lotes** de 20 proyectos:

**Ventajas**:
- ⚡ **Más rápido**: 100 proyectos = 5 llamadas vs 100 llamadas
- 💰 **Más barato**: Menos tokens consumidos
- 🛡️ **Más robusto**: Menos riesgo de rate limiting
- 📊 **Mejor consistencia**: Gemini ve el contexto completo

**Ejemplo**:
```
Scraping: 50 proyectos extraídos
   ↓
Clasificación: 3 lotes (20 + 20 + 10)
   ↓
   Lote 1: ✅ 20 proyectos clasificados
   Lote 2: ✅ 20 proyectos clasificados
   Lote 3: ✅ 10 proyectos clasificados
   ↓
Total: ✅ 50 proyectos con sector_economico
```

### Configuración de Gemini

```python
# app/services/gemini_service.py

generationConfig = {
    "temperature": 0.2,      # Baja para respuestas consistentes
    "topK": 40,
    "topP": 0.95,
    "maxOutputTokens": 2048
}
```

---

## 🎭 User-Agents Rotativos

Cada vez que el scraper hace una request, usa un user-agent diferente:

```python
# Automático en cada scraping
User-Agent 1: Chrome/120.0.0.0 en Windows
User-Agent 2: Firefox/121.0 en macOS
User-Agent 3: Safari/17.1 en macOS
...
```

**Beneficios**:
- ✅ Evita detección como bot
- ✅ Reduce probabilidad de bloqueo
- ✅ Simula tráfico real de usuarios

---

## 🧪 Probar la Integración

### Script de Prueba Rápida

```python
#!/usr/bin/env python3
"""
Prueba rápida de clasificación con Gemini
"""
import asyncio
from app.services.gemini_service import get_gemini_classifier

async def test_gemini():
    # Proyectos de ejemplo
    proyectos = [
        {
            "numero_camara": "001/2024C",
            "titulo": "Ley de Energías Renovables",
            "resumen": "Por la cual se promueve la energía solar y eólica"
        },
        {
            "numero_camara": "002/2024C",
            "titulo": "Reforma Tributaria",
            "resumen": "Modifica el impuesto sobre la renta"
        }
    ]
    
    # Clasificar
    classifier = get_gemini_classifier()
    resultados = await classifier.classify_batch(proyectos)
    
    # Mostrar
    for r in resultados:
        print(f"{r['numero_camara']}: {r['sector_economico']}")

asyncio.run(test_gemini())
```

**Resultado esperado**:
```
001/2024C: Minero-Energético
002/2024C: Tributario y Fiscal
```

---

## 📊 Costos Estimados (Gemini Pro)

### Plan Gratuito
- **Límite**: 60 requests por minuto
- **Tokens**: ~1M tokens gratis al mes
- **Nuestro uso**: ~500 tokens por batch de 20 proyectos
- **Capacidad**: ~40,000 proyectos/mes gratis ✅

### Ejemplo Real
```
Scraping de 100 proyectos:
   - Requests: 5 (batches de 20)
   - Tokens: ~2,500 tokens
   - Costo: GRATIS (plan gratuito)
   - Tiempo: ~10 segundos
```

---

## 🔧 Troubleshooting

### Error: "GEMINI_API_KEY no encontrada"

**Solución**: Verificar archivo `.env`

```bash
cd scraper-service
cat .env  # Debe mostrar GEMINI_API_KEY=AIzaSy...
```

### Error: "Rate limit exceeded"

**Solución**: Reducir tamaño de batch

```python
# En gemini_service.py
await classifier.classify_batch(proyectos, batch_size=10)  # Default: 20
```

### Error: "Invalid API key"

**Solución**: Verificar clave en Google AI Studio
- https://makersuite.google.com/app/apikey

### Clasificación incorrecta

**Solución**: Ajustar temperatura

```python
# En gemini_service.py, línea ~150
"temperature": 0.1,  # Más bajo = más consistente (default: 0.2)
```

---

## 💡 Tips y Mejores Prácticas

### 1. Usar Batch Siempre
```python
# ✅ BUENO: Batch de proyectos
resultados = await classifier.classify_batch(proyectos)

# ❌ MALO: Uno por uno
for proyecto in proyectos:
    resultado = await classifier.classify_single(proyecto)
```

### 2. Manejar Errores Gracefully
```python
try:
    resultados = await classifier.classify_batch(proyectos)
except Exception as e:
    logger.warning(f"Clasificación falló: {e}")
    # Continuar sin clasificación
    resultados = proyectos  # Sin sector_economico
```

### 3. Logging Detallado
```python
# En .env
LOG_LEVEL=DEBUG  # Ver todas las llamadas a Gemini
```

### 4. Cachear Resultados (Futuro)
```python
# TODO: Implementar caché para proyectos ya clasificados
# Evitar reclasificar el mismo proyecto
```

---

## 🎯 Arquitectura de la Solución

```
┌─────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO                       │
└─────────────────────────────────────────────────────────┘

1. Usuario hace request:
   POST /api/scrape/colombia?max_pages=1&classify=true
   
2. Scraper extrae proyectos:
   [10 proyectos] → lista de dicts
   
3. GeminiClassifier.classify_batch():
   ├─ Batch 1: [proyecto 1-10]
   │    ↓
   │  Gemini API
   │    ↓
   │  [clasificaciones]
   └─ Agregar sector_economico a cada proyecto
   
4. Respuesta:
   {
     "total_proyectos": 10,
     "proyectos": [...con sector_economico]
   }
```

---

## 📚 Archivos Creados

```
✅ NUEVOS:
   app/services/gemini_service.py      (Servicio Gemini - 250 líneas)
   app/services/__init__.py
   app/scrapers/user_agents.py         (User-agents rotativos)
   .env                                 (Variables de entorno)
   .env.example                         (Template)
   .gitignore                          (Ignora .env)

🔄 MODIFICADOS:
   app/api/routes.py                   (Agrega parámetro classify)
   app/scrapers/selenium.py            (Usa user-agents rotativos)
   requirements.txt                    (Agrega httpx, python-dotenv)
```

---

## ✨ Resultado Final

### Lo que tienes ahora:

✅ **Clasificación automática** con Gemini AI  
✅ **Batch processing** (eficiente y económico)  
✅ **User-agents rotativos** (evita detección)  
✅ **Variables de entorno** (seguridad)  
✅ **Manejo de errores** robusto  
✅ **Endpoint `/api/gemini/sectores`** (ver sectores)  
✅ **Parámetro `classify`** (activar/desactivar)  

### Ejemplo de uso completo:

```bash
# Scraping con clasificación AI
curl -X POST "http://localhost:8000/api/scrape/colombia?max_pages=2" | jq

# Respuesta:
{
  "success": true,
  "message": "Scraping de Colombia - Camara completado con clasificación AI. 20 proyectos extraídos.",
  "total_proyectos": 20,
  "proyectos": [
    {
      "numero_camara": "472/2025C",
      "titulo": "LEY CATASTRO MULTIPROPÓSITO",
      "sector_economico": "Tributario y Fiscal"  ← ✨
    },
    {
      "numero_camara": "473/2025C",
      "titulo": "LEY IMPUESTO DE RODAMIENTO",
      "sector_economico": "Tributario y Fiscal"  ← ✨
    }
    ...
  ]
}
```

---

## 🎉 ¡Integración Completada!

**Tu scraper ahora tiene:**
- 🤖 Inteligencia Artificial (Gemini Pro)
- 🎭 Evasión de detección (User-agents)
- 💰 Eficiencia de costos (Batch processing)
- 🔒 Seguridad (Variables de entorno)

**¡Listo para clasificar miles de proyectos automáticamente! 🚀**

