## Написать SQL-скрипт, который преобразует таблицу 

Исходная таблица:

| id  | stage | srage_name   | stage_value | created         |
|:----|:------|:-------------|:------------|:----------------|
| 333 | 1     | presconing   | 3           | 26.01.2024 0:01 |
| 332 | 1     | verification | true        | 26.01.2024 0:02 |
| 333 | 1     | underwriting | success     | 26.01.2024 0:03 |
| 334 | 2     | scoring      | 4           | 26.01.2024 0:04 |
| 335 | 2     | documents    | true        | 26.01.2024 0:05 |
| 336 | 2     | sale         | done        | 26.01.2024 0:06 |
| 337 | 2     | abs          | 6           | 26.01.2024 0:07 |

Агрегат:

| id  | stage | presconing | verification | underwriting | scoring | documents | sale | abs  | date_start       | date_end        |
|-----|-------|------------|--------------|--------------|---------|-----------|------|------|------------------|-----------------|
| 1   | 1     | 3          | true         | success      | null    | null      | null | null | 26.01.2024 0:01  | 26.01.2024 0:03 |
| 2   | 2     | null       | null         | null         | 4       | true      | done | 6    | 26.01.2024 0:04  | 26.01.2024 0:07 |

### Выполнение

#### 1. Создаем БД 
```bash
psql -U postgres -d postgres -c "CREATE DATABASE mv_test WITH OWNER postgres ENCODING 'UTF8';"
```

#### 2. Переходим в БД и создаем исходную таблицу т вставляем данные
```bash
psql -U postgres -W mv_test
```
```sql
CREATE TABLE sql_task_1 (
    id INT,
    stage INT,
    stage_name VARCHAR(255),
    stage_value TEXT, -- используем TEXT для универсальности
    created TIMESTAMP
);
```
```sql
INSERT INTO sql_task_1 (id, stage, stage_name, stage_value, created) VALUES
(333, 1, 'presconing', '3', '2024-01-26 00:01'),
(332, 1, 'verification', 'true', '2024-01-26 00:02'),
(333, 1, 'underwriting', 'success', '2024-01-26 00:03'),
(334, 2, 'scoring', '4', '2024-01-26 00:04'),
(335, 2, 'documents', 'true', '2024-01-26 00:05'),
(336, 2, 'sale', 'done', '2024-01-26 00:06'),
(337, 2, 'abs', '6', '2024-01-26 00:07');

```

#### 3. Создаем аггрегат
```sql
-- Предположим, что первая таблица называется stages_details, а вторая таблица, в которую мы хотим агрегировать данные, называется stages_summary.
SELECT
  MIN(id) AS id, -- предполагаем, что id уникален и его можно агрегировать как минимальное значение для группы
  stage,
  MAX(CASE WHEN stage_name = 'presconing' THEN stage_value END) AS presconing,
  MAX(CASE WHEN stage_name = 'verification' THEN stage_value END) AS verification,
  MAX(CASE WHEN stage_name = 'underwriting' THEN stage_value END) AS underwriting,
  MAX(CASE WHEN stage_name = 'scoring' THEN stage_value END) AS scoring,
  MAX(CASE WHEN stage_name = 'documents' THEN stage_value END) AS documents,
  MAX(CASE WHEN stage_name = 'sale' THEN stage_value END) AS sale,
  MAX(CASE WHEN stage_name = 'abs' THEN stage_value END) AS abs,
  MIN(created) AS date_start,
  MAX(created) AS date_end
FROM sql_task_1
GROUP BY stage
ORDER BY id;

```

