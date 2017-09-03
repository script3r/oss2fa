from tenants.models import Integration

from rest_framework.authentication import BasicAuthentication
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions


class DefaultBasicAuthentication(BasicAuthentication):

    def authenticate_credentials(self, userid, password):
        integration = Integration.objects.filter(access_key=userid).first()

        print integration.secret_key, password
        if not integration or (integration.secret_key != password):
            raise exceptions.AuthenticationFailed(
                _('Invalid access key or secret key'))

        return (None, integration)
