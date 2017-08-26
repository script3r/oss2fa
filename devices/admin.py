from django.contrib import admin

from .models import DeviceKind, Device, DeviceSelection


class DeviceKindAdmin(admin.ModelAdmin):
    list_display = ['name', 'module']
    list_filter = ['module']
    search_fields = ['name', 'description']


class DeviceAdmin(admin.ModelAdmin):
    list_display = ['kind', 'client', 'created_at']
    list_filter = ['kind', 'created_at']
    search_fields = ['kind', 'client']
    readonly_fields = ['client', 'enrollment', 'kind']


class DeviceSelectionAdmin(admin.ModelAdmin):
    list_display = ['kind']


admin.site.register(DeviceKind, DeviceKindAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(DeviceSelection, DeviceSelectionAdmin)
