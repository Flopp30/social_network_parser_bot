"""Этот скрипт изменяет код в зависимой библиотеке (TikTokApi)"""


def modify_file(file_path, line_number, old_text, new_text):
    with open(file_path) as file:
        lines = file.readlines()

    if line_number - 1 < len(lines):
        lines[line_number - 1] = lines[line_number - 1].replace(old_text, new_text)

    with open(file_path, 'w') as file:
        file.writelines(lines)


if __name__ == '__main__':
    target_file = '/usr/local/lib/python3.11/site-packages/TikTokApi/api/user.py'
    modify_file(target_file, 119, '"count": count', '"count": 30')
