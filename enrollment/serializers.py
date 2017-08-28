from __future__ import unicode_literals

from rest_framework import serializers

from devices.models import DeviceSelection
from tenants.serializers import BindingContextSerializer
from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ('pk', 'device_selection', 'username', 'status', 'created_at',
                  'expires_at', 'public_details')


class CreateEnrollmentSerializer(serializers.Serializer):
    username = serializers.CharField()
    binding_context = BindingContextSerializer(required=False)


class DevicePreparationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceSelection
        fields = ('kind', 'options')
