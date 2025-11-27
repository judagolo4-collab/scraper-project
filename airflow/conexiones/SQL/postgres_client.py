import psycopg2
from psycopg2.extras import execute_values
import logging
from typing import List, Dict, Any
import os

class PostgresClient:
    """Cliente para interactuar con PostgreSQL"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'postgres')
        self.user = os.getenv('POSTGRES_USER', 'scraper_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'scraper_pass')
        self.db = os.getenv('POSTGRES_DB', 'scraper_db')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.logger = logging.getLogger(__name__)

    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            dbname=self.db,
            port=self.port
        )

    def init_db(self):
        """Crea la tabla de proyectos si no existe"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS proyectos_ley (
            id SERIAL PRIMARY KEY,
            numero_camara VARCHAR(50),
            numero_senado VARCHAR(50),
            titulo TEXT,
            tipo VARCHAR(100),
            autores TEXT,
            estado VARCHAR(100),
            origen VARCHAR(50),
            comision VARCHAR(200),
            legislatura VARCHAR(50),
            fecha_radicacion DATE,
            resumen TEXT,
            url_detalle TEXT,
            url_pdf TEXT,
            url_gaceta TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(numero_camara, legislatura)
        );
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
            self.logger.info("✅ Tabla proyectos_ley verificada/creada")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando DB: {e}")
            raise

    def save_projects(self, proyectos: List[Dict[str, Any]]):
        """Guarda una lista de proyectos (upsert)"""
        if not proyectos:
            self.logger.warning("⚠️ No hay proyectos para guardar")
            return

        insert_sql = """
        INSERT INTO proyectos_ley (
            numero_camara, numero_senado, titulo, tipo, autores, estado, 
            origen, comision, legislatura, fecha_radicacion, resumen, 
            url_detalle, url_pdf, url_gaceta
        ) VALUES %s
        ON CONFLICT (numero_camara, legislatura) DO UPDATE SET
            titulo = EXCLUDED.titulo,
            tipo = EXCLUDED.tipo,
            autores = EXCLUDED.autores,
            estado = EXCLUDED.estado,
            origen = EXCLUDED.origen,
            comision = EXCLUDED.comision,
            fecha_radicacion = EXCLUDED.fecha_radicacion,
            resumen = EXCLUDED.resumen,
            url_detalle = EXCLUDED.url_detalle,
            url_pdf = EXCLUDED.url_pdf,
            url_gaceta = EXCLUDED.url_gaceta,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        # Preparar datos
        values = []
        for p in proyectos:
            # Convertir fecha DD/MM/YYYY a YYYY-MM-DD para Postgres
            fecha_rad = None
            if p.get('fecha_radicacion'):
                try:
                    from datetime import datetime
                    dt = datetime.strptime(p['fecha_radicacion'], '%d/%m/%Y')
                    fecha_rad = dt.strftime('%Y-%m-%d')
                except:
                    pass

            values.append((
                p.get('numero_camara'),
                p.get('numero_senado'),
                p.get('titulo'),
                p.get('tipo'),
                p.get('autores'),
                p.get('estado'),
                p.get('origen'),
                p.get('comision'),
                p.get('legislatura'),
                fecha_rad,
                p.get('resumen'),
                p.get('url_detalle'),
                p.get('url_pdf'),
                p.get('url_gaceta')
            ))

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, insert_sql, values)
            self.logger.info(f"💾 Guardados/Actualizados {len(proyectos)} proyectos")
        except Exception as e:
            self.logger.error(f"❌ Error guardando proyectos: {e}")
            raise
