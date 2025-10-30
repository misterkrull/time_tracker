from dataclasses import dataclass
from typing import Any

from exceptions import TimeTrackerError
from session import Session


@dataclass
class Activity:
    title: str
    parent_id: int
    need_show: bool
    order_number: float


class ActivitiesTable:
    def __init__(self, raw_table_data: list[tuple[Any]]):
        self._table: dict[int, Activity] = {}
        for row in raw_table_data:
            self._table[row[0]] = Activity(*row[1:])  # первое поле (ID) идёт в key, остальные - в датакласс в value

        self._validate_table()

    def _validate_table(self) -> None:
        if self.get_ordered_showing_child_ids(0) == []:
            raise TimeTrackerError("В таблице активностей нет ни одной активности, разрешённой к показу!")

        # Пробуем строить линию предков для каждой активности, чтобы исключить циклические зависимости
        # (если будет циклическая зависимость, то get_lineage_ids поднимет исключение,
        #   которое main.py перехватит и остановит всю программу)
        for activity_id in list(self._table.keys()):
            self.get_lineage_ids(activity_id)

    @property
    def count(self) -> int:
        return len(self._table.keys())

    def get_all_ids(self) -> list[int]:
        return list(self._table.keys())

    def is_top_level_activity(self, activity_id: int) -> bool:
        return self._table[activity_id].parent_id == 0

    def get_ordered_showing_child_ids(self, activity_id: int, show_hidden_activities: bool = False) -> list[int]:
        """
        Выводит список всех детей данной активности, сортирует их по order_number
        Если флаг show_hidden_activities выключен (по умолчанию), то показывает только активности,
            у которых включен флаг need_show в БД
        В противном случае не обращает внимания на need_show
        """
        return sorted(
            [
                id
                for id in self.get_all_ids()
                if self._table[id].parent_id == activity_id and (self._table[id].need_show or show_hidden_activities)
            ],
            key=lambda x: self._table[x].order_number,
        )

    def get_lineage_ids(self, id: int) -> list[int]:
        """
        Выводит список айдишников всех предков данной активности, включая её саму
        (но исключая корневую 'нулевую активность')
        """
        res: list[int] = []
        ancestor_id = id
        while ancestor_id != 0:
            res.append(ancestor_id)
            ancestor_id = self._table[ancestor_id].parent_id
            if ancestor_id in res:
                raise TimeTrackerError("В таблице активностей циклическая зависимость!")
        return res

    def get_duration_table(self, session: Session) -> dict[int, int]:
        """
        Строит таблицу длительностей активностей по текущей сессии с учётом иерархической вложенности
        ВНИМАНИЕ! Порядок добавлений элементов в итоговый словарь имеет значение,
            и определяется он строгу по порядку элементов в get_all_ids()
        """
        res = {id: 0 for id in self.get_all_ids()}
        for subs in session.subsessions:
            for id in self.get_lineage_ids(subs.activity_id):
                res[id] += subs.duration
        return res

    def get_activity_title(self, activity_id: int) -> str:
        """
        Получает название активности по айдишнику
        """
        return self._table[activity_id].title
    
    def get_activity_order_number(self, activity_id: int) -> float:
        """
        Получает порядковый номер активности по айдишнику
        """
        return self._table[activity_id].order_number