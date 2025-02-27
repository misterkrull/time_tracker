from datetime import datetime
import time

TIMERS = [1, 2, 3, 4, 5]


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
    try:
        hours, minutes, seconds = map(int, duration_str.split(":"))
    except ValueError:
        print(f"Warning: Не могу спарсить интервал {duration_str}")
        return 0

    return 3600 * hours + 60 * minutes + seconds


def time_to_string(sec: int | float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(sec))


def parse_time(datetime_str: str) -> int:
    try:
        return int(datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S").timestamp())
    except ValueError:
        print(f"Warning: Не могу спарсить время {datetime_str}")
        return 0
