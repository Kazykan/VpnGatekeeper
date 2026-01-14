import datetime
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta


def calculate_new_end_date(
    current_end_date_str: date | None, months_to_add: int
) -> date:
    """
    Рассчитывает новую дату окончания подписки.
    - Если текущая дата окончания в прошлом или отсутствует → берём сегодняшнюю дату.
    - Прибавляем указанное количество месяцев.
    - Возвращает datetime.date.
    """
    today = date.today()

    if current_end_date_str:
        current_end_date = current_end_date_str
        if current_end_date < today:
            current_end_date = today
    else:
        current_end_date = today

    new_end_date = current_end_date + relativedelta(months=months_to_add)
    return new_end_date


def calculate_new_end_date_days(
    current_end_date_str: date | None, days_to_add: int
) -> date:
    """
    Рассчитывает новую дату окончания подписки по дням.
    - Если текущая дата окончания в прошлом или отсутствует → берём сегодняшнюю дату.
    - Прибавляем указанное количество дней.
    - Возвращает datetime.date.
    """
    today = date.today()

    if current_end_date_str:
        current_end_date = current_end_date_str
        if current_end_date_str < today:
            current_end_date = today
    else:
        current_end_date = today

    new_end_date = current_end_date + timedelta(days=days_to_add)
    print(
        f"calculate new end date days: {new_end_date} old: {current_end_date_str}",
        flush=True,
    )
    return new_end_date
