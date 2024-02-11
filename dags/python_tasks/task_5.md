## Инкрементальня загрузка данных из источника с разложением в реляционную структуру

### Реализация:

#### 1. Генерируем сырые данные скприптом `json_gen.py`
#### 2. Создаем stage таблицу 
Выделяем из json дату и добавляем hash для точной идентификации строки в том случае, когда даты могут совпадать
```sql
-- готовим таблицу для работы
-- выделяем дату и сортируем по возрастанию
drop table if exists stage_json_with_date;
create table stage_json_with_date as
select
    md5(f.stage::text) as json_data_hash,
    (select to_date(jsonb_array_elements(f.stage -> 'addresses')->>'date', 'DD-MM-YYYY')
     limit 1) as date,
    f.stage as json_data
from
    fake_json_request f
order by date asc;
```
#### 3. Создаем объекты для реляционной структуры
Структура соответствует вложенности json 
```sql
-- скрипты создания объектов реляционной структуры в бд
-- схема, в которой будет располагаться новая структура
create schema if not exists test_mv;

create table if not exists test_mv.clients (
    client_id serial primary key,
    application_id int
);

create table if not exists test_mv.phones (
    phone_id serial primary key,
    client_id int references test_mv.clients(client_id),
    type varchar(255),
    number varchar(255)
);

create table if not exists test_mv.addresses (
    address_id serial primary key,
    client_id int references test_mv.clients(client_id),
    type varchar(255),
    date date,
    city varchar(255),
    street varchar(255),
    house varchar(255),
    flat int
);

create table if not exists test_mv.products (
    product_id serial primary key,
    client_id int references test_mv.clients(client_id),
    product_name varchar(255),
    count int,
    cost int,
    total_sum int
);

create table if not exists test_mv.load_metadata (
    id serial primary key,
    last_date date,
    last_hash text,
    updated_at timestamp default now()
);
```
#### 4. Выполняем вставку данных из stage в реляционные объекты испльзуя скприпт `load_data.py`
Инкрементальная загрузка реализована бачами по 100 строк через сохранение последней позиции чтения данных в таблице `load_metadata`. 
Таким образом, следующее чтение данных начиная с последней прочтенной строки и предыдущие данные не будут затронуты.

#### 5. Реализуем [DAG](https://github.com/SolonnikovDV/mvTest/blob/master/dags/test_load_dag.py) который будет выполнять инкрементальную загрузку данных каждые 5 минут
```python
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
```
