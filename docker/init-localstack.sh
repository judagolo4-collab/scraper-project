#!/bin/bash

# Script para inicializar LocalStack (S3)
set -e

echo "🚀 Inicializando LocalStack S3..."

# Crear bucket para raw data
awslocal s3 mb s3://scraper-raw-data
echo "✅ Bucket creado: scraper-raw-data"

# Crear bucket para processed data
awslocal s3 mb s3://scraper-processed-data
echo "✅ Bucket creado: scraper-processed-data"

# Configurar política pública (opcional, para desarrollo)
awslocal s3api put-bucket-acl --bucket scraper-raw-data --acl public-read
awslocal s3api put-bucket-acl --bucket scraper-processed-data --acl public-read

echo "✅ LocalStack S3 inicializado correctamente"

