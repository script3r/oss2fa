from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from devices.serializers import DeviceSerializer
from .models import Tenant, Integration


class BindingContextSerializer(serializers.Serializer):
    client_ip_address = serializers.IPAddressField(required=False)
    client_browser_fingerprint = serializers.CharField(required=False)
    trusted_device_token = serializers.CharField(required=False)


class IntegrationClientAuthDecisionSerializer(serializers.Serializer):
    username = serializers.CharField()
    binding_context = BindingContextSerializer(required=False)


class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = (
            'pk',
            'name',
            'secret_key',
            'access_key',
            'endpoint',
            'notes', )


class CreateTenantAdministratorSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()


class CreateTenantSerializer(serializers.Serializer):
    name = serializers.CharField()
    administrator = CreateTenantAdministratorSerializer()


class CreateIntegrationSerializer(serializers.Serializer):
    name = serializers.CharField()
    notes = serializers.CharField()


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = (
            'pk',
            'name', )


class IntegrationClientAuthDecisionResponseSerializer(serializers.Serializer):
    RESULT_ENROLL = 1
    RESULT_CHALLENGE = 2
    RESULT_ALLOW = 3
    RESULT_DENY = 4

    RESULT_CHOICES = (
        (
            RESULT_ENROLL,
            _('Enroll'), ),
        (
            RESULT_ENROLL,
            _('Challenge'), ),
        (
            RESULT_ENROLL,
            _('Allow'), ),
        (
            RESULT_ENROLL,
            _('Deny'), ), )

    result = serializers.ChoiceField(choices=RESULT_CHOICES)
    devices = DeviceSerializer(many=True, required=False)
