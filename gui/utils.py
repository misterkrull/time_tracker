from typing import Any

from activities import ActivitiesTable
from gui.gui_constants import DEFAULT_NEED_ID_IN_COMBOBOX_NAMES, DEFAULT_NEED_NUMBERS_IN_COMBOBOX_NAMES


def forming_combobox_names(
    activities_table: ActivitiesTable, settings: dict[str, Any]
) -> dict[int, str]:
    need_numbers_in_combobox_names: bool = settings.get(
        'need_numbers_in_combobox_names', DEFAULT_NEED_NUMBERS_IN_COMBOBOX_NAMES
    )
    need_id_in_combobox_names: bool = settings.get(
        'need_id_in_combobox_names', DEFAULT_NEED_ID_IN_COMBOBOX_NAMES
    )

    combobox_names: dict[int, str] = {}
    def add_children_to_combobox_names(id: int, pref: str):
        for num, child_id in enumerate(activities_table.get_ordered_showing_child_ids(id)):
            # кажется, будто можно убрать дублирование, но тут не всё так просто; проще выглядит с дублированием
            if need_numbers_in_combobox_names:
                combobox_names[child_id] = f"{pref}{num + 1}. {activities_table._table[child_id].name}"
                combobox_names[child_id] += f" ({child_id})" if need_id_in_combobox_names else ""
                add_children_to_combobox_names(child_id, f"{pref}{num + 1}.")
            else:
                combobox_names[child_id] = f"{pref}{activities_table._table[child_id].name}"
                combobox_names[child_id] += f" ({child_id})" if need_id_in_combobox_names else ""
                add_children_to_combobox_names(child_id, f"{pref}  ")

    add_children_to_combobox_names(0, "")
    return combobox_names
