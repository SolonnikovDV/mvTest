import psycopg2
from datetime import date as _date

from python_tasks.utils import parse_date


def create_objects_in_db(db_params: dict) -> None:
    """
    Создает объекты в базе данных с использованием начального SQL-запроса.
    :param db_params: Словарь параметров подключения к базе данных.
    """
    with psycopg2.connect(**db_params) as conn, conn.cursor() as cur:
        # Выполнение начального SQL-запроса для инициализации структуры таблицы
        with open('/Users/dmitrysolonnikov/PycharmProjects/mvideoTest/dags/python_tasks/sql/init_query.sql', 'r') as file:
            init_query = file.read()
        cur.execute(init_query)


def insert_into_clients(cur, application_id):
    """
    Вставляет нового клиента в таблицу clients и возвращает сгенерированный client_id.
    :param cur: Курсор для выполнения операций с базой данных.
    :param application_id: ID заявки.
    :return: Сгенерированный ID клиента или None в случае ошибки.
    """
    print(f"Inserting an application with application_id: {application_id}")
    try:
        # Здесь мы вставляем только application_id, позволяя PostgreSQL автоматически генерировать client_id
        cur.execute("""
            insert into test_mv.clients (application_id)
            values (%s) returning client_id
            """, (application_id,))
        # Получаем сгенерированный client_id
        client_id = cur.fetchone()[0]
        print("Successfully inserted with client_id:", client_id)
        return client_id
    except Exception as e:
        print("Error inserting into clients:", e)
        return None


def insert_into_phones(cur, client_id, phones):
    """
    Вставляет телефонные номера клиента в таблицу phones.
    :param cur: Курсор для выполнения операций с базой данных.
    :param client_id: ID клиента.
    :param phones: Список телефонных номеров клиента.
    """
    try:
        for phone in phones:
            for phone_type, number in phone.items():
                cur.execute("""
                    insert into test_mv.phones (client_id, type, number)
                    values (%s, %s, %s) on conflict do nothing
                    """, (client_id, phone_type, number))
    except Exception as e:
        print(f"Error inserting into phones: {e}")
        # Откатываем транзакцию, если произошла ошибка
        cur.connection.rollback()


def insert_into_addresses(cur, client_id, addresses):
    """
    Вставляет адреса клиента в таблицу addresses.
    :param cur: Курсор для выполнения операций с базой данных.
    :param client_id: ID клиента.
    :param addresses: Список адресов клиента.
    """
    for address in addresses:
        # Проверка на наличие данных об адресе перед попыткой их извлечения
        if address.get("address") is not None:
            address_info = address["address"]
            date_str = address.get('date')
            # Преобразование строки даты в объект datetime
            date_obj = parse_date(date_str)
            # Производим вставку данных, только если address_info не None
            cur.execute("""
                insert into test_mv.addresses (client_id, type, date, city, street, house, flat)
                values (%s, %s, %s, %s, %s, %s, %s)on conflict do nothing
                """, (
                    client_id,
                    address['type'],
                    date_obj,  # Использование преобразованной даты
                    address_info.get('city', ''),
                    address_info.get('street', ''),
                    address_info.get('house', ''),
                    address_info.get('flat', None)  # None если flat не указан
                ))
        else:
            # Обработка случаев, когда информация об адресе отсутствует
            cur.execute("""
                insert into test_mv.addresses (client_id, type, date, city, street, house, flat)
                values (%s, %s, %s, %s, %s, %s, %s) on conflict do nothing
                """, (
                    client_id,
                    address['type'],
                    None,  # Дата не указана
                    '',    # Город не указан
                    '',    # Улица не указана
                    '',    # Номер дома не указан
                    None   # Квартира не указана
                ))


def insert_into_products(cur, client_id, products):
    """
    Вставляет информацию о продуктах клиента в таблицу products.
    :param cur: Курсор для выполнения операций с базой данных.
    :param client_id: ID клиента.
    :param products: Словарь продуктов клиента.
    """
    product_cnt = products['product_cnt']
    product_cost = products['product_cost']
    for product_name, count in product_cnt.items():
        cost = product_cost.get(product_name, 0)
        cur.execute("""
            insert into test_mv.products (client_id, product_name, count, cost, total_sum)
            values (%s, %s, %s, %s, %s) on conflict do nothing
            """, (client_id, product_name, count, cost, products['total_sum']))


def update_load_metadata(cur, last_date, last_hash):
    """
    Обновляет метаданные загрузки в таблице load_metadata.
    :param cur: Курсор для выполнения операций с базой данных.
    :param last_date: Дата последней загрузки.
    :param last_hash: Хеш последней загрузки.
    """
    cur.execute("""
        insert into test_mv.load_metadata (id, last_date, last_hash, updated_at)
        values (1, %s, %s, now())
        on conflict (id) do update set last_date = excluded.last_date, last_hash = excluded.last_hash, updated_at = now();
    """, (last_date, last_hash))


# Подключение к базе данных и вставка данных
def extract_incremental_data_and_load(db_params: dict, chunk_size: int = 100):
    """
    Извлекает инкрементные данные и загружает их в базу данных.
    :param db_params: Словарь параметров подключения к базе данных.
    :param chunk_size: Размер пакета для коммита транзакции.
    """
    with psycopg2.connect(**db_params) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            # Получаем последние сохраненные метаданные загрузки
            cur.execute("select last_date, last_hash from test_mv.load_metadata order by updated_at desc limit 1;")
            last_metadata = cur.fetchone()

            last_date = last_metadata[0] if last_metadata else _date(1900, 1, 1)
            last_hash = last_metadata[1] if last_metadata else ''

            query = """
                select json_data_hash, date, json_data
                from stage_json_with_date
                where (date > %s) or (date = %s and json_data_hash > %s)
                order by date asc, json_data_hash asc
            """
            cur.execute(query, (last_date, last_date, last_hash))

            new_last_date, new_last_hash = last_date, last_hash
            record_counter = 0
            for json_data_hash, date, json_data in cur.fetchall():
                client_id = insert_into_clients(cur, json_data["application_id"])
                insert_into_phones(cur, client_id, json_data.get("phones", []))
                insert_into_addresses(cur, client_id, json_data.get("addresses", []))
                insert_into_products(cur, client_id, json_data.get("products", {}))

                record_counter += 1
                new_last_date, new_last_hash = date, json_data_hash

                if record_counter % chunk_size == 0:
                    update_load_metadata(cur, new_last_date, new_last_hash)
                    conn.commit()
                    print(f"Committed {record_counter} records.")

            # Обрабатываем оставшиеся записи, если они есть
            if record_counter % chunk_size != 0:
                update_load_metadata(cur, new_last_date, new_last_hash)
                conn.commit()
                print(f"Final commit of the last {record_counter % chunk_size} records.")

            # Если не было обработано ни одной записи, сообщаем об отсутствии новых данных
            if record_counter == 0:
                print("No new data to load.")


if __name__ == '__main__':
    # create_objects_in_db(CREDS_PG)
    # extract_incremental_data_and_load(CREDS_PG, 500)
    ...