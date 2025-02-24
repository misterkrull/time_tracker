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


def time_to_string(sec: int | float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(sec))


def time_to_sec(time_HMS: str) -> int:
    hours, minutes, seconds = map(int, time_HMS.split(":"))
    return 3600 * hours + 60 * minutes + seconds


def datetime_to_sec(datetime_Ymd_HMS: str) -> int:
    return int(datetime.strptime(datetime_Ymd_HMS, "%Y-%m-%d %H:%M:%S").timestamp())
