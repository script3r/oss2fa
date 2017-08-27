from __future__ import unicode_literals

from rest_framework import serializers

from .models import Challenge


class CreateChallengeSerializer(serializers.Serializer):
    username = serializers.CharField()
    reference = serializers.CharField(required=False)
    device_pk = serializers.IntegerField(required=False)


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = (
            'pk',
            'status',
            'public_details',
            'reference',
            'created_at',
            'expires_at', )
