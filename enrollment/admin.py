from django.contrib import admin

from .models import Enrollment


def prepare_enrollment(modeladmin, request, queryset):
    for enrollment in queryset.all():
        enrollment.prepare()


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['username', 'integration',
                    'policy', 'status', 'created_at', 'expires_at']
    list_filter = ['integration', 'policy', 'status', 'created_at']
    search_fields = ['username', 'integration', 'policy']
    readonly_fields = ['client']
    actions = [prepare_enrollment]


admin.site.register(Enrollment, EnrollmentAdmin)
