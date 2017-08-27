from django.utils.translation import ugettext_lazy as _
from rest_framework import authentication
from rest_framework import exceptions

from tenants.models import Integration


class DefaultIntegrationAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        access_key = request.META['headers'].get('X_INTEGRATION_TOKEN')
        if not access_key:
            raise exceptions.AuthenticationFailed(_('Missing integration token'))

        integration = Integration.objects.filter(access_key=access_key).first()
        if not integration:
            raise exceptions.AuthenticationFailed(_('Integration not found'))

        return (None, integration)
