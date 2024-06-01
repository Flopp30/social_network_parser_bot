import datetime

from monitoring.models import MonitoringLink


async def ensure_monitoring_link(url: str) -> tuple[MonitoringLink, bool]:
    """Обеспечивает ссылку в мониторинге (активирует/создает или просто возвращает, если уже есть)"""
    # TODO валидация ссылок
    link, create_flag = await MonitoringLink.objects.aget_or_create(
        url=url,
        defaults={
            'is_active': True,
            'next_monitoring_date': datetime.datetime.now(),
            'source': MonitoringLink.Sources.YOUTUBE if 'youtube' in url else MonitoringLink.Sources.TIKTOK,
        },
    )
    if not create_flag and not link.is_active:
        link.is_active = True
        await link.asave(update_fields=['is_active'])
    return link, create_flag
