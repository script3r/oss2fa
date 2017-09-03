from __future__ import unicode_literals

from rest_framework import serializers

from .models import Device, DeviceKind


class DeviceKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceKind
        fields = (
            'pk',
            'name',
            'description', )


class DeviceSerializer(serializers.ModelSerializer):
    kind = DeviceKindSerializer()

    class Meta:
        model = Device
        fields = (
            'pk',
            'kind',
            'name', )
