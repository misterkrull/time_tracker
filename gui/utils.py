from activities import ActivitiesTable


def forming_combobox_names(activities_table: ActivitiesTable, need_numbers_in_combobox_names: bool) -> dict[int, str]:
    combobox_names: dict[int, str] = {}
    def add_children_to_combobox_names(id: int, pref: str):
        for num, child_id in enumerate(activities_table.get_ordered_showing_child_ids(id)):
            if need_numbers_in_combobox_names:  # это первый вариант отображения
                combobox_names[child_id] = f"{pref}{num + 1}. {activities_table._table[child_id].name} ({child_id})"
                add_children_to_combobox_names(child_id, f"{pref}{num + 1}.")
            else: # это второй вариант отображения
                combobox_names[child_id] = f"{pref}{activities_table._table[child_id].name} ({child_id})"
                add_children_to_combobox_names(child_id, f"{pref}  ")

    add_children_to_combobox_names(0, "")
    return combobox_names
