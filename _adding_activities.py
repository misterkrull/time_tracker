from pathlib import Path
import sqlite3
import yaml

from common_functions import print_performance
from filenames import DEFAULT_DB_FILENAME, SETTINGS_FILENAME

@print_performance
def _adding_activities(new_activities_count: int):
    with sqlite3.connect(Path(__file__).absolute().parent / db_filename) as conn:
        cur = conn.cursor()
        for _ in range(new_activities_count):
            cur.execute(
                "INSERT INTO activities (title, parent_id, need_show, order_number)"
                "VALUES ('-', 0, 0, 0.0)"
            )
            last_id = cur.lastrowid
            new_column_name = f"sess_duration_total_act{last_id}"
            cur.execute(
                f"ALTER TABLE sessions ADD COLUMN {new_column_name}"
            )
            cur.execute(
                f"UPDATE sessions SET {new_column_name} = '00:00:00'"
            )
        conn.commit()


if __name__ == "__main__":
    settings_filepath = Path(__file__).absolute().parent / SETTINGS_FILENAME
    if settings_filepath.exists():
        with open(settings_filepath, 'r') as f:
            settings = yaml.safe_load(f)
    db_filename: str = settings.get('db_filename', DEFAULT_DB_FILENAME)

    new_activities_count = int(input("Сколько активностей добавить: "))
    _adding_activities(new_activities_count)
    input(f"Активности в количестве {new_activities_count} шт успешно добавлены!")