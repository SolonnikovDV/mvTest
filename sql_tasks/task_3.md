## Написать SQL скрипт, который из поля типа XML который соберет таблицу:


| ID | ProcessCode | IN_APPL_APPLICATIONID | IN_CURRATES_CURRENCYID | IN_CURRATES_RATE | IN_PRODUCT_TYPE | IN_PRODUCT_PARAMS_RECNUMBER | IN_PRODUCT_PARAMS_NAME | IN_PRODUCT_PARAMS_VALUE |
|----|-------------|-----------------------|------------------------|------------------|-----------------|------------------------------|------------------------|-------------------------|
| 1  | T12         | 2115                  | 810                    | 0.996            | BBP             | 1                            | TARIFFNAME             | Бизнес-Блиц предодобренный |
| 2  | T12         | 2115                  | 810                    | 0.996            | BBP             | 2                            | TARIFFID               | credit_businessBlitzP    |

### Решение
1. `xml_content` читает XML файл с помощью функции pg_read_binary_file. \
Функция `convert_from` используется для преобразования полученных данных в текстовую строку. \
Далее, полученная строка парсится как XML документ с помощью функции `xmlparse`, результат сохраняется в `xml_data`.
2. `select` выполняет выборку из `params`, генерирует ID для каждой записи с использованием оконной функции `row_number()`. \
Нумерация выполняется для каждой группы `ProcessCode` и `IN_APPL_APPLICATIONID`, и сортируется по `IN_PRODUCT_PARAMS_RECNUMBER`.

```sql
with xml_content as (
    select xmlparse(document convert_from(pg_read_binary_file('/home/request.xml'), 'UTF8')) AS xml_data
),
params as (
    select
        (xpath('/Request/Header/ProcessCode/text()', xml_data))[1]::text as ProcessCode,
        (xpath('/Request/Body/Application/Variables/IN_APPL_APPLICATIONID/text()', xml_data))[1]::text as IN_APPL_APPLICATIONID,
        (xpath('/Request/Body/Application/Categories/CURRATES/Variables/IN_CURRATES_CURRENCYID/text()', xml_data))[1]::text as IN_CURRATES_CURRENCYID,
        (xpath('/Request/Body/Application/Categories/CURRATES/Variables/IN_CURRATES_RATE/text()', xml_data))[1]::text::numeric as IN_CURRATES_RATE,
        (xpath('/Request/Body/Application/Categories/PRODUCT/Variables/IN_PRODUCT_TYPE/text()', xml_data))[1]::text as IN_PRODUCT_TYPE,
        unnest(xpath('/Request/Body/Application/Categories/PRODUCT/Categories/PRODUCT_PARAMS/Variables/IN_PRODUCT_PARAMS_RECNUMBER/text()', xml_data))::text as IN_PRODUCT_PARAMS_RECNUMBER,
        unnest(xpath('/Request/Body/Application/Categories/PRODUCT/Categories/PRODUCT_PARAMS/Variables/IN_PRODUCT_PARAMS_NAME/text()', xml_data))::text as IN_PRODUCT_PARAMS_NAME,
        unnest(xpath('/Request/Body/Application/Categories/PRODUCT/Categories/PRODUCT_PARAMS/Variables/IN_PRODUCT_PARAMS_VALUE/text()', xml_data))::text as IN_PRODUCT_PARAMS_VALUE
    from xml_content
)
select
    row_number() over (partition by ProcessCode, IN_APPL_APPLICATIONID order by IN_PRODUCT_PARAMS_RECNUMBER) as ID,
    ProcessCode,
    IN_APPL_APPLICATIONID,
    IN_CURRATES_CURRENCYID,
    IN_CURRATES_RATE,
    IN_PRODUCT_TYPE,
    IN_PRODUCT_PARAMS_RECNUMBER,
    IN_PRODUCT_PARAMS_NAME,
    IN_PRODUCT_PARAMS_VALUE
from params;
```