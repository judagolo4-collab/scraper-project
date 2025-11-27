-- Migración para soportar múltiples países
-- Ejecutar este script para actualizar la tabla existente

-- 1. Agregar columnas nuevas
ALTER TABLE proyectos_ley 
  ADD COLUMN IF NOT EXISTS country VARCHAR(50) DEFAULT 'colombia',
  ADD COLUMN IF NOT EXISTS numero VARCHAR(100),
  ADD COLUMN IF NOT EXISTS fecha_presentacion VARCHAR(20),
  ADD COLUMN IF NOT EXISTS fecha_ultima_reg VARCHAR(20),
  ADD COLUMN IF NOT EXISTS source VARCHAR(100);

-- 2. Actualizar valores existentes
UPDATE proyectos_ley 
SET 
  country = 'colombia',
  numero = COALESCE(numero_camara, numero_senado),
  source = 'camara_colombia'
WHERE country IS NULL OR numero IS NULL;

-- 3. Eliminar constraint antiguo
ALTER TABLE proyectos_ley DROP CONSTRAINT IF EXISTS unique_proyecto;
ALTER TABLE proyectos_ley DROP CONSTRAINT IF EXISTS check_numero;

-- 4. Agregar nuevo constraint único por país
ALTER TABLE proyectos_ley 
  ADD CONSTRAINT unique_proyecto_por_pais UNIQUE (country, numero);

-- 5. Crear nuevos índices
CREATE INDEX IF NOT EXISTS idx_country ON proyectos_ley(country);
CREATE INDEX IF NOT EXISTS idx_numero ON proyectos_ley(numero) WHERE numero IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_country_estado ON proyectos_ley(country, estado);

-- 6. Recrear vistas
DROP VIEW IF EXISTS proyectos_recientes CASCADE;
CREATE OR REPLACE VIEW proyectos_recientes AS
SELECT 
    id,
    country,
    COALESCE(numero, numero_camara, numero_senado) as numero,
    titulo,
    tipo,
    estado,
    legislatura,
    sector_economico,
    extracted_at
FROM proyectos_ley
ORDER BY extracted_at DESC
LIMIT 100;

DROP VIEW IF EXISTS stats_por_sector CASCADE;
CREATE OR REPLACE VIEW stats_por_sector AS
SELECT 
    country,
    sector_economico,
    COUNT(*) as total_proyectos,
    COUNT(CASE WHEN estado = 'Ley' THEN 1 END) as leyes_aprobadas,
    MAX(extracted_at) as ultima_actualizacion
FROM proyectos_ley
WHERE sector_economico IS NOT NULL
GROUP BY country, sector_economico
ORDER BY country, total_proyectos DESC;

DROP VIEW IF EXISTS stats_por_legislatura CASCADE;
CREATE OR REPLACE VIEW stats_por_legislatura AS
SELECT 
    country,
    legislatura,
    COUNT(*) as total_proyectos,
    COUNT(DISTINCT tipo) as tipos_diferentes,
    COUNT(CASE WHEN estado = 'Ley' THEN 1 END) as leyes_aprobadas,
    MAX(extracted_at) as ultima_actualizacion
FROM proyectos_ley
WHERE legislatura IS NOT NULL
GROUP BY country, legislatura
ORDER BY country, legislatura DESC;

-- 7. Nueva vista de estadísticas por país
CREATE OR REPLACE VIEW stats_por_pais AS
SELECT 
    country,
    COUNT(*) as total_proyectos,
    COUNT(DISTINCT estado) as estados_diferentes,
    COUNT(DISTINCT legislatura) as legislaturas_diferentes,
    MIN(extracted_at) as primer_registro,
    MAX(extracted_at) as ultimo_registro
FROM proyectos_ley
GROUP BY country
ORDER BY country;

