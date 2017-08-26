from django.contrib import admin

from devices.models import Device
from .models import Tenant, Integration, Client, ClientGroup


class IntegrationInline(admin.StackedInline):
    model = Integration


class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'last_updated_at']
    search_fields = ['name']
    inlines = [IntegrationInline]


class ClientDeviceInline(admin.StackedInline):
    model = Device


class ClientAdmin(admin.ModelAdmin):
    list_display = ['username', 'created_at',
                    'integration', 'group', 'email']
    search_fields = ['name', 'username', 'group', 'email']
    list_filter = ['group', 'integration', 'created_at']
    inlines = [ClientDeviceInline]


class ClientGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']


admin.site.register(Tenant, TenantAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(ClientGroup, ClientGroupAdmin)
