from typing import Any

from activities import ActivitiesTable
from gui.gui_constants import DEFAULT_NEED_ID_IN_COMBOBOX_NAMES, DEFAULT_NEED_NUMBERS_IN_COMBOBOX_NAMES


def forming_combobox_names(  # TODO переименовать, возможный вариант: activities_hierarhically
    activities_table: ActivitiesTable,
    settings: dict[str, Any],
    show_hidden_activities: bool = False,
    duration_table: dict[int, int] | None = None,
) -> dict[int, str]:
    """
    Формирует список активностей в иерархическом порядке,
    форматированный для последующего отображения пользователю

    show_hidden_activities - учитывает активности, показ которых выключен
        (может пригодиться для показа старых сессий, в которых есть ныне отключенные активности)

    duration_table - если прилагается таблица длительностей, то упорядочивание будет сделано согласно ей
    """
    need_numbers_in_combobox_names: bool = settings.get(
        'need_numbers_in_combobox_names', DEFAULT_NEED_NUMBERS_IN_COMBOBOX_NAMES
    )
    need_id_in_combobox_names: bool = settings.get(
        'need_id_in_combobox_names', DEFAULT_NEED_ID_IN_COMBOBOX_NAMES
    )

    combobox_names: dict[int, str] = {}
    def add_children_to_combobox_names(id: int, prefix: str):
        children: list[int] = activities_table.get_ordered_showing_child_ids(id, show_hidden_activities)
        if duration_table is not None:
            children = sorted(children, key=lambda x: duration_table[x], reverse=True)
        for num, child_id in enumerate(children):
            # кажется, будто можно убрать дублирование, но тут не всё так просто; проще выглядит с дублированием
            if need_numbers_in_combobox_names and duration_table is None:
                combobox_names[child_id] = f"{prefix}{num + 1}. {activities_table.get_activity_title(child_id)}"
                combobox_names[child_id] += f" ({child_id})" if need_id_in_combobox_names else ""
                add_children_to_combobox_names(child_id, f"{prefix}{num + 1}.")
            else:
                combobox_names[child_id] = f"{prefix}{activities_table.get_activity_title(child_id)}"
                combobox_names[child_id] += f" ({child_id})" if need_id_in_combobox_names else ""
                add_children_to_combobox_names(child_id, f"{prefix}  ")

    add_children_to_combobox_names(0, "")
    return combobox_names
