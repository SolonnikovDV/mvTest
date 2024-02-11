from datetime import datetime, date


def parse_date(date_str):
    """Преобразует дату из строки формата DD-MM-YYYY в объект datetime.date.
    Если date_str уже является объектом date, возвращает его.
    """
    if isinstance(date_str, date):  # Проверяем, является ли date_str объектом date
        return date_str
    elif isinstance(date_str, str):  # Проверяем, является ли date_str строкой
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").date()
        except ValueError as v:
            print(f'Ошибка формата даты: {v}')
            return None
    else:
        return None
