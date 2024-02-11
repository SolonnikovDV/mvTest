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