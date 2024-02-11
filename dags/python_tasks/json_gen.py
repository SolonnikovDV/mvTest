import json
import random
from datetime import datetime, timedelta

import psycopg2

from ini import CREDS_PG, JSON_PATH


def generate_phone():
    """
    Генерирует случайный номер телефона.
    :return: Строка, представляющая случайный номер телефона из 10 цифр.
    """
    return "".join([str(random.randint(0, 9)) for _ in range(10)])


def generate_date():
    """
    Генерирует случайную дату в диапазоне от 1 января 1950 года до 31 декабря 2020 года.
    :return: Строка, представляющая случайную дату в формате "DD-MM-YYYY".
    """
    start_date = datetime(1950, 1, 1)
    end_date = datetime(2020, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.strftime("%d-%m-%Y")


def generate_record():
    """
    Генерирует случайную запись с информацией о заявке, клиенте, телефонах, адресах и продуктах.
    :return: Словарь, содержащий сгенерированную информацию.
    """
    return {
        "application_id": random.randint(1, 100),
        "client_id": random.randint(1, 50),
        "phones": [
            {"mobile": generate_phone()},
            {"work": generate_phone()},
            {"home": generate_phone()}
        ],
        "addresses": [
            {"type": "registration", "date": generate_date(), "address": {"city": "moscow", "street": "Ленина", "house": "1", "flat": 2}},
            {"type": "residential", "date": generate_date(), "address": {"city": "moscow", "street": "Ленина", "house": "2", "flat": 3}},
            {"type": "work", "date": None, "address": None}
        ],
        "products": {
            "product_cnt": {
                "pensil": random.randint(1, 10),
                "pen": random.randint(1, 10)
            },
            "product_cost": {
                "pensil": 100,
                "pen": 10
            },
            "total_sum": random.randint(100, 500)
        }
    }


def save_json(json_path: str):
    """
    Сохраняет 100000 сгенерированных записей в файл JSON.
    :param json_path: Путь к файлу, в который будут сохранены данные.
    """
    records = [generate_record() for _ in range(100000)]

    # Замените 'path_to_your_file.json' на путь, куда вы хотите сохранить файл
    with open(json_path, 'w') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def prepare_to_stage(db_params: dict):
    """
    Подготавливает таблицу из сырых данных
    :param db_params:
    :return:
    """
    with open('python_tasks/sql/prepare_to_stage.sql', 'r') as file:
        query = file.read()
    with psycopg2.connect(**db_params) as conn, conn.cursor() as cur:
        cur.execute(query)


def load_to_stage(db_params: dict, json_path: str, batch_size: int = 1000):
    """
    Загружает данные из JSON-файла в таблицу PostgreSQL.
    :param db_params: Словарь с параметрами подключения к базе данных.
    :param json_path: Путь к JSON-файлу с данными для загрузки.
    :param batch_size: Размер пакета для побатчевой вставки данных.
    """
    with psycopg2.connect(**db_params) as conn, conn.cursor() as cur:
        # Создание таблицы, если она не существует
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fake_json_request (
                id serial,
                stage jsonb
            );
            """)
        # Загрузка данных из JSON-файла
        with open(json_path, 'r') as file:
            data = json.load(file)
            # Подготовка данных для побатчевой вставки
            batch = [(json.dumps(record),) for record in data]

            # Вставка данных побатчево
            for i in range(0, len(batch), batch_size):
                cur.executemany("""
                                INSERT INTO fake_json_request (stage)
                                VALUES (%s)
                            """, batch[i:i + batch_size])
                conn.commit()


if __name__ == '__main__':
    save_json(JSON_PATH)
    load_to_stage(CREDS_PG, JSON_PATH)
