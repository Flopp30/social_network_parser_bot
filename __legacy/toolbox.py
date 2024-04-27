import json
from datetime import datetime, timezone, timedelta
import time
import re


# import phonenumbers

def youtube_convert_to_timestamp(time_string):
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    datetime_obj = datetime.strptime(time_string, time_format)
    timestamp = datetime_obj.timestamp()
    return int(timestamp)


def get_duration_in_seconds(duration):
    duration = duration.replace('PT', '')
    if 'M' in duration:
        M_pos = duration.index('M')
        minutes = int(duration[:M_pos])
        seconds = int(duration[M_pos + 1:duration.index('S')]) if 'S' in duration else 0
        duration_in_seconds = minutes * 60 + seconds
    else:
        duration_in_seconds = int(duration[:duration.index('S')])
    return duration_in_seconds


def digZero(n):
    return f"{n:,}".replace(',', ' ')


def getLink(link, text):
    return f'<a href="{link}">{text}</a>'


def moreThan(date_string, days=1):
    date_object = datetime.strptime(date_string.split('+')[0], "%Y-%m-%dT%H:%M:%S")  # 2023-09-03T20:00:00
    current_date = datetime.now()
    time_difference = current_date - date_object
    # print(f"{time_difference=}")
    return True if time_difference > timedelta(days=days) else False


def TM():
    return f"{datetime.now():%d-%m-%Y %H:%M:%S}"


def verify_phone_number(phone_number):
    try:
        # Пытаемся преобразовать введенный номер телефона в объект PhoneNumber
        parsed_number = phonenumbers.parse(phone_number, None)
        # Проверяем, является ли номер телефона допустимым
        if phonenumbers.is_valid_number(parsed_number):
            # Возвращаем True, если номер телефона действителен
            return True
        else:
            # Возвращаем False, если номер телефона недействителен
            return False
    except phonenumbers.phonenumberutil.NumberParseException:
        # Возвращаем False, если введенный номер телефона не может быть распознан
        return False


def verify_username(username):
    regex = r"^[a-zA-Z0-9._]+$"
    if re.match(regex, username):
        return True
    else:
        return False


def verify_date(date_string):
    try:
        date_string = date_string.replace(',', '.').replace('/', '.')

        data_arr = date_string.split('.')
        if len(data_arr[-1]) > 2: data_arr[-1] = data_arr[-1][2:]
        date_string = ".".join(data_arr)
        date = datetime.strptime(date_string, "%d.%m.%y")
        print(f"{date=}\t{datetime.now()=}")
        return date_string if date > datetime.now() else False
    except ValueError:
        return False


def getChannelLink(username, title):
    return f"<a href='https://t.me/{username}'>{title}</a>"


def func_chunk(lst, n):  # Рубим список по n элементов
    for x in range(0, len(lst), n):
        e_c = lst[x: n + x]
        # if len(e_c) < n: e_c = e_c + [None for _ in range(n - len(e_c))]
        yield e_c


def date_str(time_num, utc=False, seconds=False, day_only=False):
    time_int = int(time_num)
    if time_int is None: return "НЕИЗВЕСТНО"
    if time_int > 1670000000000: time_int = time_int // 1000
    form_str = '%H:%M:%S' if seconds else '%d/%m/%y %H:%M'
    if day_only: form_str = '%d/%m/%Y'
    return datetime.fromtimestamp(time_int, tz=timezone.utc).strftime(form_str) if utc else datetime.fromtimestamp(
        time_int).strftime(form_str)


def saveFileJSON(file_name, dat):
    with open(file_name, "w", encoding='utf-8') as file: json.dump(dat, file, indent=2, ensure_ascii=False)


def openFileJSON(file_name, no=None):
    if no is None:
        no = {}
    try:
        return json.loads(open(file_name, "r", encoding='utf-8').read())
    except Exception as e:
        print(f'Error open {file_name}\n{e}')
        return no


def main():
    print(get_duration_in_seconds('PT45M17S'))
    # print(digZero(10000000))


if __name__ == '__main__':
    main()
   