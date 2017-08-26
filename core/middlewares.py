from __future__ import unicode_literals

from rest_framework import authentication

from tenants.models import Integration


class MFAHMACSignatureAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        integration = Integration.objects.first()

        return (None, integration)

