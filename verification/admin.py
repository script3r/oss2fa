from django.contrib import admin

from .models import Verification


class VerificationAdmin(admin.ModelAdmin):
    list_display = ['integration', 'delivery_method', 'destination', 'expires_at']
    list_filter = ['integration', 'delivery_method', 'expires_at']
    search_fields = ['integration', 'destination']


admin.site.register(Verification, VerificationAdmin)
