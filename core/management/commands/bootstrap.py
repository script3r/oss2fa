from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from devices.models import DeviceKind
from tenants.models import Tenant, Integration
from devices.modules import otp

import os


class Command(BaseCommand):
    help = 'Perform bootstrap operations for oss2fa'

    def handle(self, *args, **options):
        user = User.objects.filter(username=os.getenv('OSS2FA_ADMIN_USERNAME')).first()

        if user:
            return

        if not user:
            _ = User.objects.create_superuser(
                os.getenv('OSS2FA_ADMIN_USERNAME'),
                os.getenv('OSS2FA_ADMIN_EMAIL'),
                os.getenv('OSS2FA_ADMIN_PASSWORD')
            )

        DeviceKind.objects.create(
            name='OTP',
            module='devices.modules.otp.OTPDeviceKindModule',
            description='OTP Devices',
            configuration={
                'issuer_name': otp.OTPConfiguration.DEFAULT_ISSUER,
                'digits': otp.OTPConfiguration.DEFAULT_DIGITS,
                'algorithm': otp.OTPConfiguration.ALGORITHM_SHA1,
                'secret_length': otp.OTPConfiguration.DEFAULT_SECRET_LENGTH,
                'valid_window': otp.OTPConfiguration.DEFAULT_VALID_WINDOW,
                'interval': otp.OTPConfiguration.DEFAULT_INTERVAL,
            })

        tenant = Tenant.create(
            name=Tenant.DEFAULT_TENANT_NAME,
            email=os.getenv('OSS2FA_ADMIN_EMAIL'),
            password=os.getenv('OSS2FA_ADMIN_PASSWORD'),
        )

        integration = Integration.create(
            tenant=tenant,
            name=Integration.DEFAULT_INTEGRATION_NAME,
            notes='Default Integration'
        )

        message = '''
===> OSS2FA bootstrap complete!
===> To get you started, we have created a default tenant and integration.
===> Integration (name=`{0}`, access_key=`{1}`, secret_key=`{2}`)
'''
        self.stdout.write(
            self.style.SUCCESS(message.format(
                integration.name,
                integration.access_key,
                integration.secret_key
            )))
