from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta

from python_tasks.load_data import extract_incremental_data_and_load

PG_CONN = BaseHook.get_connection('pg_conn')
CREDS_PG = {
    'dbname': PG_CONN.schema,
    'user': PG_CONN.login,
    'password': PG_CONN.password,
    'host': PG_CONN.host,
    'port': PG_CONN.port
}


def wrapper_extract_incremental_data_and_load():
    extract_incremental_data_and_load(CREDS_PG, 100)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2021, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'incremental_load_dag',
    default_args=default_args,
    description='A simple DAG for incremental data loading',
    schedule_interval='*/5 * * * *',
    catchup=False,
)

run_extract_incremental_data_and_load = PythonOperator(
    task_id='extract_incremental_data_and_load',
    python_callable=wrapper_extract_incremental_data_and_load,
    dag=dag,
)
