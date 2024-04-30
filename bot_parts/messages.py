from typing import TypedDict


class MessageMap(TypedDict):
    # START
    start_not_approved: str
    start_approved: str

    # general
    link_validation_error: str

    # PARSING
    parsing_welcome: str
    parsing_success: str
    parsing_by_sec_uid: str

    # MONITORING
    monitoring_welcome: str
    # список
    monitoring_link_list_caption: str
    # добавление
    monitoring_wait_link: str
    monitoring_link_added: str
    monitoring_link_activated: str
    # удаление
    monitoring_wait_id_for_delete: str
    monitoring_link_removed: str
    monitoring_link_not_found: str


MESSAGE_MAP = MessageMap(
    start_not_approved='Привет, это Social Networks Bot. Для получения доступа обратитесь к @Afremovv',
    start_approved='О, ты получил подтверждение. Ну тогда давай приступим!',
    # general
    link_validation_error='Ссылка не валидна. Если вы считаете, что это не так - стукните в лс @Flopp',
    # PARSING
    parsing_welcome=(
        "Отправь ссылку для парсинга\n"
        "Умею:\n"
        "   - Tik-tok: user, music.\n"
        "   - Youtube: music.\n"
        "Примеры:\n<code>https://www.tiktok.com/@domixx007</code> \n\n"
        "<code>https://www.tiktok.com/music/Scary-Garry-6914598970259490818</code>\n\n"
        "<code>https://www.youtube.com/source/ZmKk4krdy84/shorts</code>\n\n"
    ),
    parsing_success='Ссылка прошла валидацию, задача на парсинг поставлена.',
    parsing_by_sec_uid='Запущен парсинг по ID',
    # MONITORING
    monitoring_welcome=(
        'Раздел мониторинга. (пока только youtube)\n'
        'Добавление - добавляет по URL.\n'
        'Отслеживаемые ссылки - возвращает эксель со списком ссылок на отслеживании.\n'
        'Удаление - удаляет по ID (брать из списка для отслеживания) или по URL'
    ),
    monitoring_link_list_caption='Количество отслеживаемых ссылок: {is_active}, всего ссылок {total}',
    # добавление
    monitoring_wait_link='Пришлите ссылку для добавления её в мониторинг',
    monitoring_link_added='Ссылка добавлена для мониторинга: {link}',
    monitoring_link_activated='Мониторинг по ссылке включен: {link}',
    # удаление
    monitoring_wait_id_for_delete='Пришлите id или url трека для удаления',
    monitoring_link_removed='Ссылка успешно удалена',
    monitoring_link_not_found='Ссылка не найдена.',
)
