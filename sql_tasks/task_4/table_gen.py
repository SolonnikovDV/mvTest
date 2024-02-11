import random
import uuid
from datetime import datetime, timedelta

import pandas as pd
import psycopg2

from ini import CREDS_PG


def random_date_2024() -> datetime:
    """
    Генерирует случайную дату в пределах 2023-2024гг.
    :return: Случайная дата в 2023-2024гг году.
    :rtype: datetime
    """
    start = datetime(2023, 1, 1)
    end = datetime(2024, 12, 31)
    delta = end - start
    random_days = random.randrange(delta.days)
    return start + timedelta(days=random_days)


def create_df(col_1: str, col_2: str, range_count: int) -> pd.DataFrame:
    """
    Создает DataFrame с заданным количеством случайных записей.
    :param col_1: Название первой колонки (UUID).
    :type col_1: str
    :param col_2: Название второй колонки (Дата).
    :type col_2: str
    :param range_count: Количество записей в DataFrame.
    :type range_count: int
    :return: DataFrame с двумя колонками и заданным количеством записей.
    :rtype: pd.DataFrame
    """
    data = {
        col_1: [str(uuid.uuid4()) for _ in range(range_count)],
        col_2: [random_date_2024() for _ in range(range_count)]
    }
    return pd.DataFrame(data)


def load_data_to_db(df: pd.DataFrame, table_name: str, db_params: dict) -> None:
    """
    Загружает данные из DataFrame в указанную таблицу базы данных.
    :param df: DataFrame с данными для вставки.
    :type df: pd.DataFrame
    :param table_name: Имя целевой таблицы в базе данных.
    :type table_name: str
    :param db_params: Словарь с параметрами подключения к базе данных.
    :type db_params: dict
    """
    with psycopg2.connect(**db_params) as conn, conn.cursor() as cur:
        # Выполнение начального SQL-запроса для инициализации структуры таблицы
        with open('sql/init_query.sql', 'r') as file:
            init_query = file.read()
        cur.execute(init_query)

        # Подготовка и выполнение запроса на вставку данных
        insert_query = f"INSERT INTO {table_name} ({df.columns[0]}, {df.columns[1]}) VALUES (%s, %s);"
        for _, row in df.iterrows():
            cur.execute(insert_query, (row[df.columns[0]], row[df.columns[1]]))
        conn.commit()


def call_delete_old_partitions(db_params: dict) -> None:
    """
    Вызывает процедуру delete_old_partitions в базе данных PostgreSQL.
    :param db_params: Словарь с данными для вставки.
    :type db_params: dict
    """
    # Установление соединения с базой данных
    with psycopg2.connect(**db_params) as conn, conn.cursor() as cur:
        # Вызов процедуры delete_old_partitions
        cur.execute("CALL delete_old_partitions();")


def run_data_load() -> None:
    """
    Исполняющий функции create_df() load_data_to_db() и блок кода
    :return:None
    """
    data = create_df('name', 'date', 10000)
    print(data)
    load_data_to_db(data, 'monthly_partitioned_table', CREDS_PG)


if __name__ == '__main__':
    run_data_load()
    call_delete_old_partitions(CREDS_PG)
