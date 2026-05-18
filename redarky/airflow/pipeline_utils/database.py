import psycopg2
from airflow.pipeline_utils.config import PG_CONN_STR

def get_postgres_connection():
    return psycopg2.connect(PG_CONN_STR)