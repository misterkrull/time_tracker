from datetime import datetime
import time


def time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Функция '{func.__name__}' выполнена за {1000 * (end_time - start_time):.3f} миллисекунд.")
        return result
    return wrapper


def sec_to_time(sec: int | float) -> str:
    sec = int(sec)
    hours, remainder = divmod(sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def time_to_sec(HMS: str) -> int:
    hours, minutes, seconds = map(int, HMS.split(':'))
    return 3600 * hours + 60 * minutes + seconds


# версия той же функции с обработкой ошибок -- может пригодится
# def time_to_sec(time: str) -> int:
#     try:
#         hours, minutes, seconds = map(int, time.split(':'))
#         return 3600 * hours + 60 * minutes + seconds
#     except:  # TODO сделать тут нормальную обработку ошибок
#         return 0


def sec_to_datetime(sec: int | float) -> str:
    return time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.gmtime(time.localtime(sec))
    )


def datetime_to_sec(Ymd_HMS: str) -> int:
    return int(datetime.strptime(Ymd_HMS, "%Y-%m-%d %H:%M:%S").timestamp())


if __name__ == "__main__":
    print(sec_to_time(8667))