# Generated by Django 4.2.11 on 2024-05-04 15:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='MonitoringLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(unique=True, verbose_name='URL адрес')),
                ('source', models.CharField(choices=[('youtube', 'Youtube'), ('tiktok', 'Tiktok')], max_length=20, verbose_name='Источник')),
                ('next_monitoring_date', models.DateTimeField(verbose_name='Дата следующего мониторинга')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна?')),
            ],
            options={
                'verbose_name': 'Ссылка для мониторинга',
                'verbose_name_plural': 'Ссылки для мониторинга',
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'max_link_per_process_count',
                    models.PositiveIntegerField(default=1000, verbose_name='Максимальное количество ссылок для парсинга за один запуск'),
                ),
                ('min_monitoring_timeout', models.PositiveIntegerField(default=24, verbose_name='Минимальный таймаут между запусками мониторинга (в часах)')),
                ('max_monitoring_count', models.PositiveIntegerField(default=10, verbose_name='Количество записываемых запусков мониторинга')),
                (
                    'min_monitoring_count_before_report',
                    models.PositiveIntegerField(default=3, verbose_name='Минимальное количество отслеживаний перед созданием отчёта'),
                ),
                ('alert_ratio', models.FloatField(default=1.5, verbose_name='Коэффициент оповещения')),
                ('chats_id_for_alert', models.CharField(max_length=500, verbose_name='id чатов для оповещений (разделитель - запятая)')),
            ],
            options={
                'verbose_name': 'Конфигурация',
                'verbose_name_plural': 'Конфигурации',
            },
        ),
        migrations.CreateModel(
            name='MonitoringResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_count', models.PositiveIntegerField(blank=True, null=True, verbose_name='Количество видео')),
                ('created_at', models.DateTimeField(auto_now=True, verbose_name='Дата создания')),
                (
                    'monitoring_link',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='results', to='monitoring.monitoringlink', verbose_name='Ссылка'
                    ),
                ),
            ],
            options={
                'verbose_name': 'Результат мониторинга',
                'verbose_name_plural': 'Результаты мониторинга',
            },
        ),
    ]
