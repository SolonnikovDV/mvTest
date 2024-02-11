-- основная таблица
drop table if exists monthly_partitioned_table cascade;
create table if not exists monthly_partitioned_table (
    id serial,
    name varchar(255),
    date date not null
) partition by range (date);

-- функция, распределяющая по партициям
drop function if exists check_partition_existence;
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

-- создание триггера вызывающего функцию распределения по партициям
drop trigger if exists trigger_before_insert_monthly_partitioned_table on monthly_partitioned_table;
create trigger trigger_before_insert_monthly_partitioned_table
before insert on monthly_partitioned_table
for each row execute function check_partition_existence();

-- создание партиций на 2024 год
do $$
declare
    iter_date date := '2023-01-01';
    end_date date := '2024-12-31';
begin
    while iter_date < end_date loop
        execute format($f$
            create table if not exists monthly_partitioned_table_%1$s
            partition of monthly_partitioned_table
            for values from ('%2$s') to ('%3$s')
        $f$, to_char(iter_date, 'yyyy_mm'), iter_date, (iter_date + interval '1 month'));

        iter_date := iter_date + interval '1 month';
    end loop;
end$$;

-- процедура удаления партиции старше 2 мес от текущей даты
drop procedure if exists delete_old_partitions();
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