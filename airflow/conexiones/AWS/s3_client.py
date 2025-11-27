# s3_client.py - Cliente para interactuar con S3 (LocalStack)

import boto3
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class S3Client:
    """Cliente para guardar y recuperar datos en S3"""
    
    def __init__(self):
        """Inicializa el cliente S3 con configuración de LocalStack"""
        self.endpoint_url = os.getenv('AWS_ENDPOINT_URL', 'http://localstack:4566')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', 'test')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
        
        logger.info(f"✅ S3 Client initialized (endpoint: {self.endpoint_url})")
    
    def save_raw_data(
        self,
        data: List[Dict[str, Any]],
        country: str,
        institution: str,
        execution_date: str
    ) -> str:
        """
        Guarda datos raw en S3
        
        :param data: Lista de proyectos
        :param country: País (ej: colombia)
        :param institution: Institución (ej: camara)
        :param execution_date: Fecha de ejecución (YYYY-MM-DD)
        :return: S3 key del archivo guardado
        """
        bucket = 'scraper-raw-data'
        
        # Crear key: raw/country/institution/YYYY/MM/DD/data.json
        date_obj = datetime.strptime(execution_date, '%Y-%m-%d')
        s3_key = (
            f"raw/{country}/{institution}/"
            f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/"
            f"data_{datetime.now().strftime('%H%M%S')}.json"
        )
        
        # Convertir a JSON
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        
        # Subir a S3
        self.s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'country': country,
                'institution': institution,
                'execution_date': execution_date,
                'total_records': str(len(data))
            }
        )
        
        logger.info(f"✅ Raw data saved to S3: s3://{bucket}/{s3_key}")
        logger.info(f"📊 Total records: {len(data)}")
        
        return f"s3://{bucket}/{s3_key}"
    
    def save_processed_data(
        self,
        data: List[Dict[str, Any]],
        country: str,
        institution: str,
        execution_date: str
    ) -> str:
        """
        Guarda datos procesados en S3
        
        :param data: Lista de proyectos procesados
        :param country: País
        :param institution: Institución
        :param execution_date: Fecha de ejecución
        :return: S3 key del archivo guardado
        """
        bucket = 'scraper-processed-data'
        
        date_obj = datetime.strptime(execution_date, '%Y-%m-%d')
        s3_key = (
            f"processed/{country}/{institution}/"
            f"{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/"
            f"data_{datetime.now().strftime('%H%M%S')}.json"
        )
        
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        
        self.s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'country': country,
                'institution': institution,
                'execution_date': execution_date,
                'total_records': str(len(data))
            }
        )
        
        logger.info(f"✅ Processed data saved to S3: s3://{bucket}/{s3_key}")
        
        return f"s3://{bucket}/{s3_key}"
    
    def list_files(self, bucket: str, prefix: str) -> List[str]:
        """
        Lista archivos en S3
        
        :param bucket: Nombre del bucket
        :param prefix: Prefijo para filtrar
        :return: Lista de keys
        """
        response = self.s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return []
        
        return [obj['Key'] for obj in response['Contents']]
    
    def read_json(self, bucket: str, key: str) -> List[Dict[str, Any]]:
        """
        Lee un archivo JSON desde S3
        
        :param bucket: Nombre del bucket
        :param key: Key del objeto
        :return: Datos parseados
        """
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)

