from django.contrib import admin

from .models import Challenge


class ChallengeAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'device', 'policy', 'status', 'created_at', 'expires_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['client', 'device']


admin.site.register(Challenge, ChallengeAdmin)
