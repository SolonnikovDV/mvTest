-- готовим таблицу для работы
-- выделяем дату и сортируем по возрастанию
drop table if exists stage_json_with_date;
create table stage_json_with_date as
select
    md5(f.stage::text) as json_data_hash,
    (select TO_DATE(jsonb_array_elements(f.stage -> 'addresses')->>'date', 'DD-MM-YYYY')
     limit 1) as date,
    f.stage as json_data
from
    fake_json_request f
order by date asc;