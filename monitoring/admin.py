from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from monitoring.models import (
    Parameter,
    MonitoringLink,
    MonitoringResult
)


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = (
        'max_link_per_process_count',
        'min_monitoring_timeout',
        'max_monitoring_count',
        'min_monitoring_count_before_report',
        'alert_ratio',
        'chats_id_for_alert',
    )

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if object_id is None and Parameter.objects.exists():
            obj = Parameter.objects.first()
            return HttpResponseRedirect(reverse('admin:monitoring_parameter_change', args=(obj.pk,)))
        return super().changeform_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request):
        if Parameter.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(MonitoringLink)
class MonitoringLinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'is_active', 'source', 'next_monitoring_date',)
    search_fields = ('url', 'source',)
    list_filter = ('is_active', 'source',)


@admin.register(MonitoringResult)
class MonitoringResultAdmin(admin.ModelAdmin):
    list_display = ('url', 'video_count', 'created_at',)
    search_fields = ('url',)
    list_filter = ('created_at',)

    def url(self, obj):
        return obj.monitoring_link.url

    url.short_description = 'Link url'
