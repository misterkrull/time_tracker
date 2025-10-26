import yaml
from pathlib import Path
from typing import Any

from filenames import SETTINGS_FILENAME

# Этот файл требуется для запуска db_manager, а последний используется в main.py и в tools/tt.py
# Поскольку они оба концептуально связаны и должны обслуживать один и тот же сеттинг файлов,
#   а также во избежание дублирования кода,
# был создан этот файл.

def load_settings() -> dict[str, Any]:
    settings = {}
    settings_filepath = Path(__file__).absolute().parent / SETTINGS_FILENAME
    if settings_filepath.exists():
        with open(settings_filepath, "r") as f:
            settings = yaml.safe_load(f)

    return settings
