from django.db import models
from django.db.models import TextChoices


class Parameter(models.Model):
    max_link_per_process_count = models.PositiveIntegerField(
        default=1000,
        verbose_name='Количество ссылок для парсинга',
        help_text='Максимальное количество ссылок для парсинга за один запуск',
    )
    max_link_per_run_count = models.PositiveIntegerField(
        default=10,
        verbose_name='Количество ссылок для парсинга',
        help_text='Максимальное количество ссылок для парсинга за одну итерацию',
    )
    monitoring_iteration_timeout_seconds = models.PositiveIntegerField(
        default=60,
        verbose_name='Таймаут между итерациями',
        help_text='Таймаут между итерациями мониторинга (в секундах)'
    )
    min_monitoring_timeout = models.PositiveIntegerField(
        default=8,
        verbose_name='Таймаут между запусками мониторинга',
        help_text='Минимальный таймаут между запусками мониторинга (в часах) для одной ссылки',
    )
    max_monitoring_count = models.PositiveIntegerField(
        default=10,
        verbose_name='Количество записываемых запусков мониторинга'
    )
    min_monitoring_count_before_report = models.PositiveIntegerField(
        default=3,
        verbose_name='Минимальное количество отслеживаний',
        help_text='Минимальное количество отслеживаний перед созданием отчёта',
    )
    alert_ratio = models.FloatField(
        verbose_name='Коэффициент оповещения',
        default=1.5
    )
    chats_id_for_alert = models.CharField(
        verbose_name='id чатов для оповещений',
        help_text='(разделитель - запятая)',
        max_length=500,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Конфигурация'
        verbose_name_plural = 'Конфигурации'

    def __str__(self):
        return f"Конфигурация параметров (ID {self.pk})"


class MonitoringLink(models.Model):
    class Sources(TextChoices):
        YOUTUBE = 'youtube'
        TIKTOK = 'tiktok'

    url = models.URLField(
        verbose_name='URL адрес',
        unique=True
    )

    source = models.CharField(
        verbose_name='Источник',
        choices=Sources.choices,
        max_length=20
    )

    next_monitoring_date = models.DateTimeField(
        verbose_name='Дата следующего мониторинга'
    )

    is_active = models.BooleanField(
        verbose_name='Активна?',
        default=True
    )

    class Meta:
        verbose_name = 'Ссылка для мониторинга'
        verbose_name_plural = 'Ссылки для мониторинга'

    def __str__(self):
        return f'{self.id} :: {self.url}'


class MonitoringResult(models.Model):
    monitoring_link = models.ForeignKey(
        MonitoringLink,
        verbose_name='Ссылка',
        on_delete=models.CASCADE,
        related_name='results'
    )
    video_count = models.PositiveIntegerField(
        verbose_name='Количество видео',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Результат мониторинга'
        verbose_name_plural = 'Результаты мониторинга'

    def __str__(self):
        return f"{self.monitoring_link.url} - {self.video_count}"
