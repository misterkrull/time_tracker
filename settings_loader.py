import yaml
from pathlib import Path
from typing import Any

from filenames import SETTINGS_FILENAME


DEFAULT_SETTINGS = {
    "enable_global_hotkeys": True,

    "timer_frame_count": 3,

    "main_window_x": 678,
    "main_window_y": 250,
    "main_window_position_x": 678,
    "main_window_position_y": -768,

    "combobox_height": 20,

    "need_activity_numbers_in_combobox_names": False,
    "need_activity_ids_in_combobox_names": True,
    "need_activity_numbers_in_tt_stat": False,
    "need_activity_ids_in_tt_stat": True
}


def load_settings() -> dict[str, Any]:
    settings = DEFAULT_SETTINGS.copy()
    settings_filepath = Path(__file__).absolute().parent / SETTINGS_FILENAME
    if settings_filepath.exists():
        with open(settings_filepath, "r") as f:
            settings.update(yaml.safe_load(f))
    return settings
