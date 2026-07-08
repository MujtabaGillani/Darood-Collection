from django.contrib import admin

from .models import DaroodEntry


@admin.register(DaroodEntry)
class DaroodEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'count', 'date', 'recorded_by', 'created_at')
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'
    autocomplete_fields = ()
