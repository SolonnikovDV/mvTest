### Таски
Описание - ссылка на пошаговое описание выполнения задания \
Расположение - ссылка на физическое расположение скриптов 

<hr>

| Задание | Описание | Расположение |
|---------|----------|--------------|
| Таск 1  | Написать SQL-скрипт, который преобразует таблицу [Описание](https://github.com/SolonnikovDV/mvTest/blob/master/sql_tasks/task_1.md) |[Расположение](https://github.com/SolonnikovDV/mvTest/tree/master/sql_tasks)  |
| Таск 2  | Реализовать календарь на весь 2024 [Описание](https://github.com/SolonnikovDV/mvTest/blob/master/sql_tasks/task_2.md) |[Расположение](https://github.com/SolonnikovDV/mvTest/tree/master/sql_tasks)  |
| Таск 3  | Написать SQL скрипт, который из поля типа XML, во вложении соберет таблицу [Описание](https://github.com/SolonnikovDV/mvTest/blob/master/sql_tasks/task_3.md)|[Расположение](https://github.com/SolonnikovDV/mvTest/tree/master/sql_tasks)  |
| Таск 4  | Создать таблицу с автоматическим партиционированием по месячным партициям и процедуру удаления партиций старше 2 мес. от текущей даты [Описание](https://github.com/SolonnikovDV/mvTest/blob/master/sql_tasks/task_4/task_4.md) |[Расположение](https://github.com/SolonnikovDV/mvTest/tree/master/sql_tasks)  |
| Таск 5  | Настроить ежедневную инкрементную выгрузку из источника (PostgreSQL) и разложение в реляционную структуру БД только свежих записей [Описание](https://github.com/SolonnikovDV/mvTest/blob/master/dags/python_tasks/task_5.md) |[Расположение](https://github.com/SolonnikovDV/mvTest/tree/master/dags/python_tasks)  |
| Таск 6  | Составить реляционную структуру БД в виде DDL (SQL, YML или XML) [Описание](https://github.com/SolonnikovDV/mvTest/blob/master/dags/python_tasks/task_6.xml)|[Расположение](https://github.com/SolonnikovDV/mvTest/tree/master/dags/python_tasks)  |
| Таск 7  | Запуск максимально простой: в проекте нужны скрипты python и requirements.txt, проект должен запускаться по инструкции в readme для девопса [Описание](https://github.com/SolonnikovDV/mvTest/blob/master/csv_dowload/task_7.md)|[Расположение](https://github.com/SolonnikovDV/mvTest/tree/master/csv_dowload)  |

<br> 

#### Инструкция к таску 5 
##### Запуск поекта инкрементальной загрузки данных из таблицы в БД
1. Проект использует скприты загрузки исполняемые по расписанию через `DAG` в `airflow`.
2. Для развертывания `airflow`  в докер подготовлен [docker-compose.yml](https://github.com/SolonnikovDV/mvTest/blob/master/docker-compose.yaml) \
   Для старта контенера выполнить из директории проекта где распложена структура `dags` , `logs`, `plugins` следующую команду

```bash
docker-compose up -d
```

3. Либо перенести проект `python_tasks` и  `test_load_dag.py` на целевое пространство, где уже развернут `airflow`.
<hr>
