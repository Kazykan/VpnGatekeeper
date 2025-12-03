from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def calculate_new_end_date(current_end_date_str: str | None, months_to_add: int) -> str:
    """
    Рассчитывает новую дату окончания подписки.
    - Если текущая дата окончания в прошлом или отсутствует → берём сегодняшнюю дату.
    - Прибавляем указанное количество месяцев.
    - Возвращаем строку в формате YYYY-MM-DD.
    """
    now = datetime.now()

    if current_end_date_str:
        current_end_date = datetime.strptime(current_end_date_str, "%Y-%m-%d")
        if current_end_date < now:
            current_end_date = now
    else:
        current_end_date = now

    new_end_date = current_end_date + relativedelta(months=months_to_add)
    return new_end_date.strftime("%Y-%m-%d")


def calculate_new_end_date_days(
    current_end_date_str: str | None, days_to_add: int
) -> str:
    """
    Рассчитывает новую дату окончания подписки по дням.
    - Если текущая дата окончания в прошлом или отсутствует → берём сегодняшнюю дату.
    - Прибавляем указанное количество дней.
    - Возвращаем строку в формате YYYY-MM-DD.
    """
    now = datetime.now()

    if current_end_date_str:
        current_end_date = datetime.strptime(current_end_date_str, "%Y-%m-%d")
        if current_end_date < now:
            current_end_date = now
    else:
        current_end_date = now

    new_end_date = current_end_date + timedelta(days=days_to_add)
    return new_end_date.strftime("%Y-%m-%d")
