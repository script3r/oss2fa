from django.contrib import admin

from .models import Policy, Rule, Configuration


class ConfigurationInline(admin.StackedInline):
    model = Configuration


class RuleInline(admin.StackedInline):
    model = Rule


class PolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration', 'created_at']
    list_filter = ['integration', 'created_at']
    search_fields = ['integration', 'name']
    inlines = [RuleInline, ConfigurationInline]


admin.site.register(Policy, PolicyAdmin)
