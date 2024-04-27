from django.contrib import admin

from monitoring.models import (Parameter,
                               MonitoringLink,
                               MonitoringResult)


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    pass


@admin.register(MonitoringLink)
class MonitoringLinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'next_monitoring_date',)


@admin.register(MonitoringResult)
class MonitoringResultAdmin(admin.ModelAdmin):
    list_display = ('monitoring_link', 'video_count', 'created_at',)
