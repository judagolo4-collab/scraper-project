# postgres_client.py - Cliente para interactuar con PostgreSQL

import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class PostgresClient:
    """Cliente para guardar y recuperar datos en PostgreSQL"""
    
    def __init__(self, database: str = 'proyectos_ley'):
        """
        Inicializa el cliente PostgreSQL
        
        :param database: Nombre de la base de datos
        """
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.user = os.getenv('POSTGRES_USER', 'airflow')
        self.password = os.getenv('POSTGRES_PASSWORD', 'airflow')
        self.database = database
        
        self.conn = None
        self.cursor = None
        
        logger.info(f"✅ PostgresClient initialized (db: {database})")
    
    def connect(self):
        """Establece conexión con la base de datos"""
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.conn.cursor()
        logger.info("✅ Connected to PostgreSQL")
    
    def close(self):
        """Cierra la conexión"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("🔒 PostgreSQL connection closed")
    
    def create_tables(self):
        """Crea las tablas necesarias si no existen"""
        create_proyectos_table = """
        CREATE TABLE IF NOT EXISTS proyectos (
            id SERIAL PRIMARY KEY,
            numero_camara VARCHAR(50),
            numero_senado VARCHAR(50),
            titulo TEXT NOT NULL,
            tipo VARCHAR(100),
            autores TEXT,
            estado VARCHAR(100),
            origen VARCHAR(100),
            comision VARCHAR(200),
            legislatura VARCHAR(50),
            fecha_radicacion DATE,
            resumen TEXT,
            url_detalle TEXT,
            url_pdf TEXT,
            url_gaceta TEXT,
            sector_economico VARCHAR(100),
            pais VARCHAR(50) NOT NULL,
            institucion VARCHAR(50) NOT NULL,
            fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            s3_raw_path TEXT,
            UNIQUE(numero_camara, pais, institucion)
        );
        
        CREATE INDEX IF NOT EXISTS idx_pais_institucion ON proyectos(pais, institucion);
        CREATE INDEX IF NOT EXISTS idx_legislatura ON proyectos(legislatura);
        CREATE INDEX IF NOT EXISTS idx_sector_economico ON proyectos(sector_economico);
        CREATE INDEX IF NOT EXISTS idx_fecha_extraccion ON proyectos(fecha_extraccion);
        """
        
        create_metadata_table = """
        CREATE TABLE IF NOT EXISTS scraper_metadata (
            id SERIAL PRIMARY KEY,
            pais VARCHAR(50) NOT NULL,
            institucion VARCHAR(50) NOT NULL,
            execution_date DATE NOT NULL,
            total_records INTEGER,
            new_records INTEGER,
            updated_records INTEGER,
            s3_raw_path TEXT,
            s3_processed_path TEXT,
            execution_time_seconds FLOAT,
            status VARCHAR(50),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(pais, institucion, execution_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_metadata_pais ON scraper_metadata(pais, institucion);
        CREATE INDEX IF NOT EXISTS idx_metadata_date ON scraper_metadata(execution_date);
        """
        
        self.cursor.execute(create_proyectos_table)
        self.cursor.execute(create_metadata_table)
        self.conn.commit()
        
        logger.info("✅ Tables created/verified")
    
    def get_last_extraction_date(self, pais: str, institucion: str) -> Optional[str]:
        """
        Obtiene la última fecha de extracción exitosa
        
        :param pais: País
        :param institucion: Institución
        :return: Fecha en formato YYYY-MM-DD o None
        """
        query = """
        SELECT MAX(execution_date)
        FROM scraper_metadata
        WHERE pais = %s AND institucion = %s AND status = 'success'
        """
        
        self.cursor.execute(query, (pais, institucion))
        result = self.cursor.fetchone()
        
        if result and result[0]:
            return result[0].strftime('%Y-%m-%d')
        
        return None
    
    def insert_proyectos(
        self,
        proyectos: List[Dict[str, Any]],
        pais: str,
        institucion: str,
        s3_raw_path: str
    ) -> Dict[str, int]:
        """
        Inserta proyectos en la base de datos (ON CONFLICT UPDATE)
        
        :param proyectos: Lista de proyectos
        :param pais: País
        :param institucion: Institución
        :param s3_raw_path: Path de S3 donde está el raw data
        :return: Dict con contadores de new y updated
        """
        if not proyectos:
            return {'new': 0, 'updated': 0}
        
        insert_query = """
        INSERT INTO proyectos (
            numero_camara, numero_senado, titulo, tipo, autores,
            estado, origen, comision, legislatura, fecha_radicacion,
            resumen, url_detalle, url_pdf, url_gaceta, sector_economico,
            pais, institucion, s3_raw_path
        ) VALUES %s
        ON CONFLICT (numero_camara, pais, institucion)
        DO UPDATE SET
            numero_senado = EXCLUDED.numero_senado,
            titulo = EXCLUDED.titulo,
            tipo = EXCLUDED.tipo,
            autores = EXCLUDED.autores,
            estado = EXCLUDED.estado,
            origen = EXCLUDED.origen,
            comision = EXCLUDED.comision,
            legislatura = EXCLUDED.legislatura,
            fecha_radicacion = EXCLUDED.fecha_radicacion,
            resumen = EXCLUDED.resumen,
            url_detalle = EXCLUDED.url_detalle,
            url_pdf = EXCLUDED.url_pdf,
            url_gaceta = EXCLUDED.url_gaceta,
            sector_economico = EXCLUDED.sector_economico,
            fecha_extraccion = CURRENT_TIMESTAMP,
            s3_raw_path = EXCLUDED.s3_raw_path
        RETURNING (xmax = 0) AS inserted;
        """
        
        # Preparar valores
        values = []
        for p in proyectos:
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
                p.get('fecha_radicacion'),
                p.get('resumen'),
                p.get('url_detalle'),
                p.get('url_pdf'),
                p.get('url_gaceta'),
                p.get('sector_economico'),
                pais,
                institucion,
                s3_raw_path
            ))
        
        # Ejecutar bulk insert
        execute_values(self.cursor, insert_query, values)
        
        # Contar inserts vs updates
        results = self.cursor.fetchall()
        new_count = sum(1 for r in results if r[0])  # xmax = 0 significa insert
        updated_count = len(results) - new_count
        
        self.conn.commit()
        
        logger.info(f"✅ Proyectos guardados: {new_count} nuevos, {updated_count} actualizados")
        
        return {'new': new_count, 'updated': updated_count}
    
    def save_metadata(
        self,
        pais: str,
        institucion: str,
        execution_date: str,
        total_records: int,
        new_records: int,
        updated_records: int,
        s3_raw_path: str,
        s3_processed_path: str,
        execution_time: float,
        status: str = 'success',
        error_message: str = None
    ):
        """
        Guarda metadata de la ejecución
        
        :param pais: País
        :param institucion: Institución
        :param execution_date: Fecha de ejecución
        :param total_records: Total de registros procesados
        :param new_records: Registros nuevos
        :param updated_records: Registros actualizados
        :param s3_raw_path: Path de S3 raw
        :param s3_processed_path: Path de S3 processed
        :param execution_time: Tiempo de ejecución en segundos
        :param status: Estado (success/error)
        :param error_message: Mensaje de error si aplica
        """
        insert_query = """
        INSERT INTO scraper_metadata (
            pais, institucion, execution_date, total_records,
            new_records, updated_records, s3_raw_path, s3_processed_path,
            execution_time_seconds, status, error_message
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (pais, institucion, execution_date)
        DO UPDATE SET
            total_records = EXCLUDED.total_records,
            new_records = EXCLUDED.new_records,
            updated_records = EXCLUDED.updated_records,
            s3_raw_path = EXCLUDED.s3_raw_path,
            s3_processed_path = EXCLUDED.s3_processed_path,
            execution_time_seconds = EXCLUDED.execution_time_seconds,
            status = EXCLUDED.status,
            error_message = EXCLUDED.error_message,
            created_at = CURRENT_TIMESTAMP
        """
        
        self.cursor.execute(insert_query, (
            pais, institucion, execution_date, total_records,
            new_records, updated_records, s3_raw_path, s3_processed_path,
            execution_time, status, error_message
        ))
        
        self.conn.commit()
        
        logger.info("✅ Metadata saved")

