from django.contrib import admin

from user.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'is_approved', 'chat_id', 'username', 'last_visit_time', 'registration_datetime', 'state'
    )
    list_filter = (
        'last_visit_time',
        'registration_datetime',
        'state'
    )
    ordering = ('-id', 'username', 'last_visit_time')
    search_fields = ('username', 'state')
    list_per_page = 50
