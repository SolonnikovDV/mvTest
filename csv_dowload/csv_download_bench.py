import dask
dask.config.set({'dataframe.query-planning': True})
import dask.dataframe as dd
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import time
import pyarrow.csv as pc
import csv


CREDS_PG = {
    'dbname': 'mv_test',
    'user': 'postgres',
    'password': 'postgrespw',
    'host': 'localhost',
    'port': 55001
}
CSV_PATH_INPUT = 'csv_download/csv/2011-capitalbikeshare-tripdata.csv'
CSV_PATH_OUTPUT = 'csv_download/csv/changed.csv'
CONN_STR = "postgresql+psycopg2://postgres:postgrespw@localhost:55001/mv_test"

# Замена делиметра в csv "," -> ";"
def replace_delimiter_in_csv(input_file_path, output_file_path, original_delimiter=',', new_delimiter=';'):
    with open(input_file_path, 'r', encoding='utf-8') as input_file:
        with open(output_file_path, 'w', encoding='utf-8', newline='') as output_file:
            reader = csv.reader(input_file, delimiter=original_delimiter)
            writer = csv.writer(output_file, delimiter=new_delimiter)

            for row in reader:
                writer.writerow(row)


# Использование COPY команды PostgreSQL
def load_csv_with_copy(csv_file_path, table_name, db_params):
    with psycopg2.connect(**db_params) as conn, conn.cursor() as cur:
        with open(csv_file_path, 'r') as f:
            cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER DELIMITER ','", f)
        conn.commit()


# Использование pandas и SQLAlchemy
def load_csv_with_pandas(csv_file_path, table_name, connection_string):
    df = pd.read_csv(csv_file_path)
    engine = create_engine(
        connection_string,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600
    )
    df.to_sql(table_name, engine, if_exists='replace', index=False, method='multi', chunksize=10000)


# Использование Dask для обработки больших данных
def load_csv_with_dask(csv_file_path, table_name, connection_string):
    ddf = dd.read_csv(csv_file_path)
    engine = create_engine(
        connection_string,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600
    )
    for partition in ddf.to_delayed():
        pd_df = partition.compute()
        pd_df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')


# Использование Pyarrow для обработки больших данных
def load_csv_with_pyarrow(csv_file_path, table_name, connection_string):
    arrow_table = pc.read_csv(csv_file_path)
    df = arrow_table.to_pandas()
    engine = create_engine(
        connection_string,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600
    )
    df.to_sql(name=table_name, con=engine, if_exists='replace', index=False, method='multi', chunksize=10000)


# Бенчмаркинг
def benchmark(func, *args, **kwargs):
    start_time = time.time()
    # Вызов функции с передачей аргументов
    func(*args, **kwargs)
    end_time = time.time()
    print(f"Время выполнения: {end_time - start_time} секунд.")


if __name__ == '__main__':
    # метод "COPY команды PostgreSQL" требует предварительного анализа csv и создание соответствующего объекта в БД,
    # что не удовлетворяет условиям загрузки данных "на лету"
    # benchmark(func=load_csv_with_copy, csv_file_path=CSV_PATH, table_name='pg_csv_copy', db_params=CREDS_PG)

    # pandas и SQLAlchemy
    # Время выполнения: 16.544862985610962 секунд.
    benchmark(func=load_csv_with_pandas, csv_file_path=CSV_PATH_OUTPUT, table_name='pg_csv_pandas', connection_string=CONN_STR)

    # Dask
    # Время выполнения: 17.20434594154358 секунд.
    benchmark(func=load_csv_with_dask, csv_file_path=CSV_PATH_OUTPUT, table_name='pg_csv_dask', connection_string=CONN_STR)

    # PyArrow
    # Время выполнения: 15.28524112701416 секунд.
    benchmark(func=load_csv_with_pyarrow, csv_file_path=CSV_PATH_OUTPUT, table_name='pg_csv_arrow', connection_string=CONN_STR)
