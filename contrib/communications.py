from __future__ import unicode_literals

from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from core.errors import MFAError


class DjangoSMTPMailer(object):
    class Configuration(serializers.Serializer):
        pass

    class Request(serializers.Serializer):
        from_email = serializers.EmailField()
        recipient = serializers.EmailField()
        subject = serializers.CharField()
        message = serializers.CharField()
        html_message = serializers.CharField(required=False)

    def __init__(self, options):
        self._options = options

    def get_configuration_model(self, data):
        return DjangoSMTPMailer.Configuration(data=data)

    def get_request_model(self, data):
        return DjangoSMTPMailer.Request(data=data)

    def execute(self, request):
        assert request.is_valid()

        data = request.validated_data

        res = send_mail(
            data['subject'],
            data['message'],
            data['from_email'],
            [data['recipient']]
        )

        if res == 0:
            return False, MFAError(_('Could not send mail'))

        return True, None
