import argparse
import sys
from pathlib import Path
from typing import Any

# Ради того, чтобы этот файл видел модули из надпапки, приходится делать вот такое
# Лёша говорит, что это костыль, но пока не очень понятно, как сделать лучше
sys.path.append(str(Path(__file__).parent.parent))

from activities import ActivitiesTable
from common_functions import duration_to_string, forming_activities_for_tt_stat, time_to_string
from db_manager import DB
from settings_loader import load_settings


def parse_range(range_string: str) -> list[int]:
    """
    (Изначально данная функция -- порождение ДипСика)
    Парсит строку с диапазонами чисел и возвращает отсортированный список уникальных значений.
    
    Формат - тот же самый, когда указываешь, какие страницы отправить на печать:
    - Отдельные числа: "1, 3, 5"
    - Диапазоны: "1-5"
    - Комбинации: "1, 3-5, 10"
    - Пробелы игнорируются: "1,3-5, 10"
    
    Args:
        range_string (str): Строка с диапазонами чисел
        
    Returns:
        list[int]: Отсортированный список уникальных чисел

    Raises:
        ValueError: Если строка содержит некорректные данные
    """
    if not range_string or not range_string.strip():
        return []
    
    numbers = set()
    
    # Разбиваем на части по запятым
    parts = [part.strip() for part in range_string.split(',') if part.strip()]

    try:    
        for part in parts:
            # Проверяем, является ли часть диапазоном
            if '-' in part:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())
                
                if start > end:
                    # Меняем местами, если диапазон указан в обратном порядке
                    start, end = end, start
               
                # Добавляем все числа в диапазоне
                numbers.update(range(start, end + 1))
            else:
            # Отдельное число
                numbers.add(int(part.strip()))    
    except ValueError:
        raise ValueError("Вы ввели некорректный диапазон") from None
    
    return sorted(numbers)


def find_max_decimal_places(numbers: list[float]) -> int:
    """Находит максимальное количество знаков после запятой"""
    max_places = 0
    for num in numbers:
        num_str = str(num)
        if "." in num_str:
            # Берем дробную часть и убираем незначащие нули справа
            decimal_part = num_str.split(".")[1].rstrip("0")
            max_places = max(max_places, len(decimal_part))
    return max_places


def addact_command(db: DB, title: str, parent_id: int, order_number: float | None, need_show: bool) -> None:
    """Реализация команды добавления новой активности"""
    
    if parent_id < 0:
        print("ID предка не может быть отрицательным")
        return

    # Если order_number не введён, то получаем его интерактивно
    if order_number is None:
        # импортируем из БД таблицу активностей
        activities_table: ActivitiesTable = db.activities_table
        # формируем список айдишников детей введёной родительской активности
        child_ids: list[int] = activities_table.get_ordered_showing_child_ids(parent_id)

        if parent_id == 0:
            print("Вы добавляете корневую активность.")
            if len(child_ids) > 0:
                print("Вот список корневых активностей с порядковыми номерами:")
            else:
                print("Корневых активностей пока нет. Будете первым!")
        else:
            print(
                f'Вы добавляете подактивность активности "{activities_table.get_activity_title(parent_id)}" ({parent_id})'
            )
            if len(child_ids) > 0:
                print("Вот список подактивностей этой активности с порядковыми номерами:")
            else:
                print("У этой активности пока нет подактивности. Будете первым!")

        # вычисляем максимальное количество знаков после точки среди порядковых номеров
        #   детей указанной родительской активности
        # это нужно для красивой отрисовки этих флоатов
        decimal_places: int = find_max_decimal_places([activities_table.get_activity_order_number(id) for id in child_ids])
        if decimal_places == 0: 
            decimal_places = 1  # один знак после точки всяко надо рисовать, чтобы подчеркнуть флоатовость
        for id in child_ids:
            print(
                f"{activities_table.get_activity_order_number(id):{4 + decimal_places}.{decimal_places}f} ",
                activities_table.get_activity_title(id)
            )

        while True:
            try:
                inputed = input("Введите порядковый номер добавляемой активности (или '-' для отмены): ")
                order_number = float(inputed)
                break
            except Exception:
                if inputed == '-':
                    print("Отмена операции")
                    return
                print("Вы ввели не число, попробуйте ещё раз!")

    print("Добавляем активность:")
    print(f"  Название: {title}")
    print(f"  parent_id: {parent_id}")
    print(f"  order_number: {order_number}")
    print(f"  need_show: {need_show}")
    db.add_activity(title, parent_id, need_show, order_number)


def stat_command(db: DB, settings: dict[str, Any], session_range: str, backward: bool, sort: bool) -> None:
    """
    Реализация команды отображения статистики
    На вход принимает диапазоны значений сессий (в формате типа "страницы к печати") 

    backward - с этим флагом отчёт сессий будет вестись с конца
    sort - с этим флагом выдача результатов будет отсортирована по длительности активностей
    """

    try:
        session_ids: list[int] = parse_range(session_range)
    except ValueError as err:
        print(str(err))
        return

    # импортируем из БД таблицу активностей
    activities_table: ActivitiesTable = db.activities_table
    # получаем список айдишников всех активностей
    all_activities_ids: list[int] = activities_table.get_all_ids()
    # получаем айдишник последней сессии
    last_session_id: int | None = db.get_last_session_id()
    if last_session_id is None:
        print("В базе данных нет ни одной сессии")
        return

    if backward:  # если флаг активен, то будем считать сессии с конца
        session_ids = [last_session_id - session_id for session_id in session_ids]

    total_duration = 0  # общая длительность всех сессий
    total_number_of_subsessions = 0  # общее количество подсессий
    total_subsessions_duration = 0  # общая длительность всех подсессиий

    # общая длительность всех активностей;  ключи - айдишники активностей, значения - время в секундах
    total_duration_table: dict[int, int] = {id: 0 for id in all_activities_ids}
    
    # счётчик количества реально существующих сессий с номерами из session_ids
    number_of_sessions = 0 

    for id in session_ids:
        session = db.get_session_by_id(id)
        if session is None:
            continue
        number_of_sessions += 1

        # добавляем длительности активностей из нашей сессии к total_duration_table и total_subsessions_duration
        duration_table = activities_table.get_duration_table(session)
        for key in all_activities_ids:
            total_duration_table[key] += duration_table[key]
            if activities_table.is_top_level_activity(key):
                total_subsessions_duration += duration_table[key]
            
        session_duration = session.end_time - session.start_time
        total_duration += session_duration

        number_of_subsessions = len(session.subsessions)
        total_number_of_subsessions += number_of_subsessions

    if number_of_sessions == 0:
        print("В указанном диапазоне сессии отсуствуют")
        return

    print()
    print(f"{number_of_sessions:8}  Количество сессий в указанном диапазоне")
    print(f"{total_number_of_subsessions:8}", " Общее количество подсессий в этих сессиях")
    print()
    
    print(
        duration_to_string(total_duration),
        " Длительность сессий"
        # " Длительность сесси" + ("и" if number_of_sessions == 1 else "й")
        #   оставил, если захочу вернуть эту фичу (но тогда надо и в другом месте делать)
    )
    print(duration_to_string(total_subsessions_duration), " Общая длительность подсессий")
    print()

    # show_hidden_activities - нужно показывать скрытые активности, т.к. в старых сессиях они могут присутстсвовать
    activities_hierarchically: dict[int, str] = forming_activities_for_tt_stat(
        activities_table, settings, sort, total_duration_table
    )
    for key in activities_hierarchically.keys():
        if total_duration_table[key]:  # игнорируем активности с нулевой длительностью: нет смысла их показывать
            print(duration_to_string(total_duration_table[key]), activities_hierarchically[key], sep='  ')

    print()


def view_command(db: DB, number_of_sessions: int) -> None:
    """Реализация команды просмотра последних сессий"""    
    if number_of_sessions <= 0:
        print("Введённое число должно быть строго положительным")
        return

    # получаем айдишник последней сессии
    last_session_id: int | None = db.get_last_session_id()
    if last_session_id is None:
        print("В базе данных нет ни одной сессии")
        return

    print(f"Список последних {number_of_sessions} сессий")
    print(
        # более длинный формат, пока оставлю, может потом сделаю чего с этим
        # "  ID      Начало сессии         Конец сессии       Длительность     Кол-во подсессий    Общая длит. подсессий"
        " ID     Начало сессии        Конец сессии      Длительность  Подсессии  Длит.подс."
    )

    for id in range(last_session_id - number_of_sessions + 1, last_session_id + 1):
        session = db.get_session_by_id(id)
        if session is None:
            continue
        # print(
        #     f"{id:4}   {time_to_string(session.start_time)}   {time_to_string(session.end_time)}     "
        #     f"{duration_to_string(session.duration)}             {session.number_of_subsessions:3}                 "
        #     f"{duration_to_string(session.duration_of_all_subsessions)}"
        # )
        print(
            f"{id:3}  {time_to_string(session.start_time)}  {time_to_string(session.end_time)}    "
            f"{duration_to_string(session.duration)}       {session.number_of_subsessions:3}      "
            f"{duration_to_string(session.duration_of_all_subsessions)}"
        )


def main():
    parser = argparse.ArgumentParser(description="Набор консольных инструментов по работе с базой данных тайм-трекера")
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    addact_parser = subparsers.add_parser("addact", help="Добавить активность")
    stat_parser = subparsers.add_parser("stat", help="Показать статистику по указанным сессиям")
    view_parser = subparsers.add_parser("view", help="Отобразить последние сессии")

    addact_parser.add_argument("title", type=str, help="Название активности")
    addact_parser.add_argument("parent_id", type=int, help="ID родительской активности (0, если активность корневая)")
    addact_parser.add_argument(
        "order_number",
        nargs="?",
        default=None,
        type=float,
        help="Порядковый номер (если не указать, то программа предложит ввести его в интерактивном режиме",
    )
    addact_parser.add_argument(  # Флаг need_show (по умолчанию True, с --no-need-show становится False)
        "--no-need-show",
        action="store_false",
        dest="need_show",
        default=True,
        help="Не показывать активность (по умолчанию: показывать)",
    )

    # nargs='+' означает, что на вход ожидается несколько аргументов (как минимум один)
    # сделано потому, чтобы можно было использовать пробелы при вводе диапазана
    # но аргпарс понимает пробелы как разделители аргументов, поэтому делаем вот так
    stat_parser.add_argument(
        "session_range", nargs="+", type=str, help="Диапазон сессий (можно использовать ',' и '-')"
    )
    stat_parser.add_argument(
        "-b",
        "--backward",
        action="store_true",
        dest="backward",
        default=False,
        help="Считать сессии в обратном порядке, с конца",
    )
    stat_parser.add_argument(
        "-s",
        "--sorted",
        action="store_true",
        dest="sort",
        default=False,
        help="Отсортировать активности по убыванию длительности",
    )

    view_parser.add_argument("number_of_sessions", type=int, help="Количество отображаемых сессий")

    args = parser.parse_args()

    settings = load_settings()  # путь в файлу настроек лежит в filenames.py
    db = DB(settings)

    if args.command == "addact":
        addact_command(db, args.title, args.parent_id, args.order_number, args.need_show)
    elif args.command == "stat":
        # нужно собрать все пришедшие (благодаря nargs='+') аргументы воедино:
        if hasattr(args, 'session_range'):
            args.session_range = ' '.join(args.session_range)
        stat_command(db, settings, args.session_range, args.backward, args.sort)
    elif args.command == "view":
        view_command(db, args.number_of_sessions)
    

if __name__ == "__main__":
    main()
