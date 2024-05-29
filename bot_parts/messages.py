import logging

log = logging.getLogger(__name__)


class MessageContainer:
    # START
    start_not_approved: str = 'Привет, это Social Networks Bot. Для получения доступа обратитесь к @Afremovv'
    start_approved: str = (
        'Парсинг:\n'
        '    - youtube music\n'
        '    - tiktok music, user\n\n'
        'Мониторинг:\n'
        '    - youtube music, profile\n'
        '    - tiktok music'
    )

    # general
    link_validation_error: str = (
        'Ссылка не валидна.\n'
        'Если вы считаете, что это не так - стукните в лс @Flopp\n\n{link}'
    )

    # PARSING
    parsing_welcome: str = (
        "Отправь ссылку для парсинга\n"
        "Умею:\n"
        "   - Tik-tok: user, music.\n"
        "   - Youtube: music.\n"
        "Примеры:\n<code>https://www.tiktok.com/@domixx007</code> \n\n"
        "<code>https://www.tiktok.com/music/Scary-Garry-6914598970259490818</code>\n\n"
        "<code>https://www.youtube.com/source/ZmKk4krdy84/shorts</code>\n\n"
    )
    parsing_success: str = 'Ссылка прошла валидацию, задача на парсинг поставлена.'
    parsing_by_sec_uid: str = 'Запущен парсинг по ID'

    # ONE LINK STAT
    one_link_stat_welcome: str = (
        'Отправь ссылку на тт видео пользователя для получения статистики'
    )

    # MONITORING
    monitoring_welcome: str = (
        'Раздел мониторинга\n'
        '(tiktok music, youtube user, youtube music)\n\n'
        '- Добавление - добавляет по URL.\n\n'
        '- Отслеживаемые ссылки - возвращает эксель со списком ссылок на отслеживании.\n\n'
        '- Удаление - удаляет по ID (брать из списка для отслеживания) или по URL'
    )
    # список
    monitoring_link_list_caption: str = (
        'Количество отслеживаемых ссылок: {is_active}\n'
        'Всего ссылок {total}'
    )
    monitoring_link_list_empty = (
        'Нет отслеживаемых ссылок.'
    )
    # добавление
    monitoring_wait_link: str = (
        'Пришлите ссылку для добавления её в мониторинг.\n'
        'Для добавления нескольких ссылок за раз - разделите их пробелом или через shift + enter'
    )
    monitoring_add_multiple_links: str = (
        'Успешно добавлено {success_count} ссылок.\n'
        'Создано: {created_count}\n'
        'Включено: {activated_count}\n'
        'Не валидны: {invalid_count}'
    )
    monitoring_add_link: str = 'Мониторинг по ссылке включен: {link}'
    # удаление
    monitoring_wait_id_for_delete: str = 'Пришлите id или url трека для удаления'
    monitoring_link_removed: str = 'Ссылка успешно удалена'
    monitoring_link_not_found: str = 'Ссылка не найдена.'
