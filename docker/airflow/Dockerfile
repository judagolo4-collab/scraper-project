# Dockerfile simplificado para Airflow
FROM apache/airflow:2.10.4-python3.11

USER airflow

# Copiar requirements y instalar
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copiar código
COPY ./dags /opt/airflow/dags
COPY ./conexiones /opt/airflow/conexiones
COPY ./plugins /opt/airflow/plugins
