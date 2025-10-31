import time
from datetime import datetime
from typing import Any

from activities import ActivitiesTable


def print_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(
            f"Функция '{func.__name__}' выполнена за {1000 * (end_time - start_time):.3f} миллисекунд."
        )
        return result

    return wrapper


def duration_to_string(sec: int | float) -> str:
    sec = int(sec)
    hours, remainder = divmod(sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def parse_duration(duration_str: str) -> int:
    hours, minutes, seconds = map(int, duration_str.split(":"))
    return 3600 * hours + 60 * minutes + seconds


def time_to_string(sec: int | float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(sec))

def time_to_string_with_weekday(sec: int | float) -> str:
    weekdays_ru = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    
    time_struct = time.localtime(sec)
    weekday_num = time_struct.tm_wday
    
    main_part = time.strftime("%Y-%m-%d ", time_struct)
    return main_part + weekdays_ru[weekday_num] + time.strftime(" %H:%M:%S", time_struct)

def parse_time(datetime_str: str) -> int:
    return int(datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S").timestamp())


def forming_activities_for_combobox(activities_table: ActivitiesTable, settings: dict[str, Any]) -> dict[int, str]:
    """
    Формирует список активностей в иерархическом порядке,
    форматированный для отображения пользователю в комбобоксах

    Возращает словарь, где ключи - айдишники активностей, а значения - форматированные названия активностей
    Порядок элементов определяется очерёдостью добавления, поэтому см. на порядок в .keys()
    
    """
    return _forming_activities_hierarhically(
        activities_table,
        settings["need_activity_numbers_in_combobox"],
        settings["need_activity_ids_in_combobox"],
        show_hidden_activities=False,
        need_others=False,  # в комбобоксах показ "прочего" не нужен
        need_sort=False,    # в комбобоксах сортировка по длительности не нужна
        duration_table={},  # т.к. need_sort=False, то duration_table использоваться не будет => неважно, что передавать
    )


def forming_activities_for_tt_stat(
    activities_table: ActivitiesTable,
    settings: dict[str, Any],
    need_others: bool,
    need_sort: bool,
    duration_table: dict[int, int],
) -> dict[int, str]:
    """
    Формирует список активностей в иерархическом порядке,
    форматированный для отображения пользователю в выдаче команды tt stat

    Может содержать скрытые активности (т.е. у которых в БД флаг need_show=0) --
    для tt stat это нужно, поскольку даже если сейчас активность скрыта, то когда-то давно 
    она могла быть отображаемой, а значит её надо включать в статистику tt stat
    
    need_others - если True, то будут отображаться строчки "прочее"
    (пригодится для случаев, если длительность активности строго меньше суммы длительностей детей)
    У "прочего" будут отрицательные ключи, по модулю равные айдишнику соответствующей активности

    need_sort - если True, то упорядочивание будет сделано согласно таблице длительностей duration_table

    Возращает словарь, где ключи - айдишники активностей, а значения - форматированные названия активностей
    Порядок элементов определяется очерёдостью добавления, поэтому см. на порядок в .keys()
    """
    return _forming_activities_hierarhically(
        activities_table,
        settings["need_activity_numbers_in_tt_stat"],
        settings["need_activity_ids_in_tt_stat"],
        show_hidden_activities=True,  # отображаем скрытые активности
        need_others=need_others,
        need_sort=need_sort,
        duration_table=duration_table,
    )


def _forming_activities_hierarhically(  # noqa: PLR0913
    activities_table: ActivitiesTable,
    need_numbers: bool,
    need_id: bool,
    show_hidden_activities: bool,
    need_others: bool,
    need_sort: bool,
    duration_table: dict[int, int]
) -> dict[int, str]:

    result: dict[int, str] = {}
    # рекурсивно обходим дерево активностей
    def add_children(id: int, prefix: str):
        children: list[int] = activities_table.get_ordered_showing_child_ids(id, show_hidden_activities)
        if need_sort:
            children = sorted(children, key=lambda x: duration_table[x], reverse=True)
        for num, child_id in enumerate(children):
            # кажется, будто можно убрать дублирование, но тут не всё так просто; проще выглядит с дублированием
            if need_numbers and not need_sort:
                result[child_id] = f"{prefix}{num + 1}. {activities_table.get_activity_title(child_id)}"
                add_children(child_id, f"{prefix}{num + 1}.")
            else:
                result[child_id] = f"{prefix}{activities_table.get_activity_title(child_id)}"
                add_children(child_id, f"{prefix}  ")
            result[child_id] += f" ({child_id})" if need_id else ""
        if need_others and id != 0:
            result[-id] = f"{prefix}{' ' if need_numbers and not need_sort else ''}прочее"
            result[-id] += f" ({id})" if need_id else ""

    add_children(0, "")
    return result