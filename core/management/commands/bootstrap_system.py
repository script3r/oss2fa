from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from devices.models import DeviceKind
from tenants.models import Tenant, Integration
from devices.modules import otp


class Command(BaseCommand):
    help = 'Perform bootstrap operations for oss2fa'

    def add_arguments(self, parser):
        parser.add_argument('admin_username', type=str, default='administrator')
        parser.add_argument('admin_email', type=str, default='admin@oss2fa.com')
        parser.add_argument('admin_password', type=str)
        parser.add_argument('integration', type=str, default='Default')

    def _generate_random_password(self):
        return '12345'

    def handle(self, *args, **options):
        user = User.objects.filter(username=options['admin_username']).first()
        password = options['admin_password'] or self._generate_random_password()

        if user:
            return

        if not user:
            _ = User.objects.create_superuser(
                options['admin_username'],
                options['admin_email'],
                password
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
            first_name=Tenant.DEFAULT_TENANT_CONTACT_FIRST_NAME,
            last_name=Tenant.DEFAULT_TENANT_CONTACT_LAST_NAME,
            email=options['admin_email'],
            password=password,
        )

        integration = Integration.create(
            tenant=tenant,
            name=Integration.DEFAULT_INTEGRATION_NAME,
            notes='Default Integration'
        )

        message = '''
===> OSS2FA bootstrap complete!
===> To get started, we have created an administrator account, a default tenant, and an integration.
===> Administrator Account (username=`{0}`, password=`{1})
===> Integration (name=`{2}`, access_key=`{3}`, secret_key=`{4}`)
'''
        self.stdout.write(
            self.style.SUCCESS(message.format(
                options['admin_username'],
                password,
                integration.name,
                integration.access_key,
                integration.secret_key
            )))
