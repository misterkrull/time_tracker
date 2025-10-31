import yaml
from pathlib import Path
from typing import Any

from filenames import DEFAULT_DB_FILENAME, SETTINGS_FILENAME


DEFAULT_SETTINGS = {
    "db_filename": DEFAULT_DB_FILENAME,

    "enable_global_hotkeys": True,

    "timer_frame_count": 3,

    "main_window_x": 678,
    "main_window_y": 250,
    "main_window_position_x": 678,
    "main_window_position_y": -768,

    "combobox_height": 20,
    "combobox_dropdown_width_increase" : 0,

    "need_activity_numbers_in_combobox": False,
    "need_activity_ids_in_combobox": True,
    "need_activity_numbers_in_tt_stat": False,
    "need_activity_ids_in_tt_stat": True,
    "need_others_in_tt_stat": True,
}


def load_settings() -> dict[str, Any]:
    settings = DEFAULT_SETTINGS.copy()
    settings_filepath = Path(__file__).absolute().parent / SETTINGS_FILENAME
    if settings_filepath.exists():
        with open(settings_filepath, "r") as f:
            settings.update(yaml.safe_load(f))

    settings["db_filepath"]: Path = Path(__file__).absolute().parent / settings["db_filename"] # type: ignore

    return settings
