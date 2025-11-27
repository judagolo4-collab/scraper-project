-- init_tables.sql - Esquema de base de datos para proyectos de ley

-- Tabla principal de proyectos (multi-país)
CREATE TABLE IF NOT EXISTS proyectos_ley (
    id SERIAL PRIMARY KEY,
    
    -- País de origen
    country VARCHAR(50) NOT NULL DEFAULT 'colombia',
    
    -- Identificadores (adaptable por país)
    numero VARCHAR(100),  -- Número genérico (Colombia: numero_camara, Perú: numero)
    numero_camara VARCHAR(50),  -- Específico Colombia
    numero_senado VARCHAR(50),  -- Específico Colombia
    
    -- Información básica
    titulo VARCHAR(500) NOT NULL,
    titulo_completo TEXT,
    tipo VARCHAR(100),
    estado VARCHAR(100),
    origen VARCHAR(50),
    
    -- Metadata
    legislatura VARCHAR(20),
    comision TEXT,
    autores TEXT,
    resumen TEXT,
    
    -- URLs
    url_detalle VARCHAR(500),
    url_pdf VARCHAR(500),
    url_gaceta VARCHAR(500),
    
    -- Fechas (Perú)
    fecha_presentacion VARCHAR(20),
    fecha_ultima_reg VARCHAR(20),
    
    -- Clasificación AI
    sector_economico VARCHAR(100),
    
    -- Source tracking
    source VARCHAR(100),
    
    -- Timestamps
    extracted_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint: por país y número
    CONSTRAINT unique_proyecto_por_pais UNIQUE (country, numero)
);

-- Índices para búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_country ON proyectos_ley(country);
CREATE INDEX IF NOT EXISTS idx_numero ON proyectos_ley(numero) WHERE numero IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_numero_camara ON proyectos_ley(numero_camara) WHERE numero_camara IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_numero_senado ON proyectos_ley(numero_senado) WHERE numero_senado IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_legislatura ON proyectos_ley(legislatura);
CREATE INDEX IF NOT EXISTS idx_estado ON proyectos_ley(estado);
CREATE INDEX IF NOT EXISTS idx_tipo ON proyectos_ley(tipo);
CREATE INDEX IF NOT EXISTS idx_sector ON proyectos_ley(sector_economico);
CREATE INDEX IF NOT EXISTS idx_extracted_at ON proyectos_ley(extracted_at DESC);
CREATE INDEX IF NOT EXISTS idx_country_estado ON proyectos_ley(country, estado);

-- Tabla de auditoría (opcional, para tracking de cambios)
CREATE TABLE IF NOT EXISTS proyectos_audit (
    audit_id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos_ley(id),
    campo_modificado VARCHAR(100),
    valor_anterior TEXT,
    valor_nuevo TEXT,
    modificado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vista para proyectos recientes
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

-- Vista para estadísticas por sector
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

-- Vista para estadísticas por legislatura
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

-- Vista para estadísticas por país
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

-- Comentarios para documentación
COMMENT ON TABLE proyectos_ley IS 'Tabla principal de proyectos de ley de Colombia';
COMMENT ON COLUMN proyectos_ley.numero_camara IS 'Número de radicación en la Cámara (ej: 472/2025C)';
COMMENT ON COLUMN proyectos_ley.numero_senado IS 'Número de radicación en el Senado';
COMMENT ON COLUMN proyectos_ley.sector_economico IS 'Sector económico clasificado por Gemini AI';
COMMENT ON COLUMN proyectos_ley.extracted_at IS 'Fecha de extracción desde el scraper';
COMMENT ON COLUMN proyectos_ley.updated_at IS 'Fecha de última actualización en la BD';

