## Создать таблицу с автоматическим партиционирование

### Решение:

#### 1. Подготовим таблицу
Cоздаем таблицу с патиционированием по date
```sql
create table if not exists monthly_partitioned_table (
    id serial,
    name varchar(255),
    date date not null
) partition by range (date);
```

#### 2. Добавим функцию обработки
Функция, которая проверяет существует ли партиция и вставляет данные
```sql
drop function if exists create_monthly_partition();
create or replace function check_partition_existence()
returns trigger as $$
declare
    partition_name text := 'monthly_partitioned_table_' || to_char(new.date, 'yyyy_mm');
begin
    -- проверка существования партиции
    if not exists(select 1 from pg_catalog.pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'public' and c.relname = partition_name) then
        raise exception 'партиция для даты % не найдена.', new.date;
    end if;
    return new;
end;
$$ language plpgsql;
```

#### 3. Для автоматизации партиционирования добавим триггера для автоматического создания партиций
Триггер будет вызывать функцию check_partition_existence перед каждой вставкой
```sql
create trigger trigger_before_insert_monthly_partitioned_table
before insert on monthly_partitioned_table
for each row execute function check_partition_existence();
```

#### 4. Создание партиций на 2024
Поскольку на текущий момент (насколько я осведомлен) PopsgreSQL не поддерживает автоматическое создание партиций "на лету" 
через триггеры при вставке строки в партиционированную таблицу.  
И если функция пытается создать партицию, но в момент, когда триггер срабатывает, строка уже проходит проверку на 
соответствие диапазону партиции, что приводит к ошибке, если подходящая партиция отсутствует. 
По этой причине предсоздадим партиции на 2024 год
```sql
-- создание партиций на 2024 год
do $$
declare
    iter_date date := '2024-01-01'; -- изменено имя переменной
    end_date date := '2024-12-31';
begin
    while iter_date < end_date loop
        execute format($f$
            create table if not exists monthly_partitioned_table_%1$s
            partition of monthly_partitioned_table
            for values from ('%2$s') to ('%3$s')
        $f$, to_char(iter_date, 'yyyy_mm'), iter_date, (iter_date + interval '1 month'));

        iter_date := iter_date + interval '1 month'; -- изменено имя переменной
    end loop;
end$$;
```


#### 5. Создадим процедуру удаления партиций старше текущей даты
```sql
-- процедура удаления партиции старше 2 мес от текущей даты
create or replace procedure delete_old_partitions()
language plpgsql
as $$
declare
    partition record;
    partition_date date;
    cutoff_date date := current_date - interval '2 months';
begin
    for partition in
        select inhrelid::regclass::text as partition_name
        from pg_inherits
        join pg_class parent on pg_inherits.inhparent = parent.oid
        join pg_class child on pg_inherits.inhrelid = child.oid
        join pg_namespace nmsp_parent on nmsp_parent.oid = parent.relnamespace
        join pg_namespace nmsp_child on nmsp_child.oid = child.relnamespace
        where parent.relname='monthly_partitioned_table'
    loop
        -- преобразование имени партиции в дату (предполагаемый формат monthly_partitioned_table_yyyy_mm)
        partition_date := to_date(split_part(partition.partition_name, '_', 4) || '-' || split_part(partition.partition_name, '_', 5) || '-01', 'yyyy-mm-dd');

        raise notice 'проверка партиции: %, дата партиции: %, дата отсечения: %', partition.partition_name, partition_date, cutoff_date;

        -- удаление партиции, если её дата меньше даты отсечения
        if partition_date < cutoff_date then
            execute 'drop table if exists public.' || quote_ident(partition.partition_name) || ' cascade;';
            raise notice 'удалена партиция: %', partition.partition_name;
        end if;
    end loop;
end;
$$;
```

#### 6. Добавим генерирование датафрейма и скриптов создания объектов и вызова процедуры в код python
Скриптом python: 
- сгенерируем датафрейм, 
- создаем в БД все необходимые объекты,  
- вставляем данные, 
- вызываем процедуру
```python
import random
import uuid
from datetime import datetime, timedelta

import pandas as pd
import psycopg2

from ini import CREDS_PG


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
```
