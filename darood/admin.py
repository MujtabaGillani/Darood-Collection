from django.contrib import admin

from .models import DaroodEntry


@admin.register(DaroodEntry)
class DaroodEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'count', 'date', 'status', 'manager', 'recorded_by', 'created_at')
    list_filter = ('status', 'date', 'manager')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'
