from django.db import models


class Parameter(models.Model):
    max_link_per_process_count = models.PositiveIntegerField(
        default=1000,
        verbose_name='Максимальное количество ссылок для парсинга за один запуск'
    )
    min_monitoring_timeout = models.PositiveIntegerField(
        default=24,
        verbose_name='Минимальный таймаут между запусками мониторинга (в часах)'
    )
    max_monitoring_count = models.PositiveIntegerField(
        default=10,
        verbose_name='Количество записываемых запусков мониторинга'
    )
    min_monitoring_count_before_report = models.PositiveIntegerField(
        default=3,
        verbose_name='Минимальное количество отслеживаний перед созданием отчёта'
    )

    class Meta:
        verbose_name = 'Конфигурация'
        verbose_name_plural = 'Конфигурации'

    def __str__(self):
        return f"Конфигурация параметров (ID {self.pk})"


class MonitoringLink(models.Model):
    url = models.URLField(
        verbose_name='URL адрес',
        unique=True
    )
    next_monitoring_date = models.DateTimeField(
        verbose_name='Дата следующего мониторинга'
    )

    class Meta:
        verbose_name = 'Ссылка для мониторинга'
        verbose_name_plural = 'Ссылки для мониторинга'

    def __str__(self):
        return self.url


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
