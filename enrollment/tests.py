import datetime

import pyotp
from django.test import TestCase
from django.utils import timezone

from contrib.models import Module
from devices.models import DeviceKind
from devices.modules.email import EmailDevicePrivateEnrollmentDetails, EmailDeviceHandlerEnrollmentPreparation
from devices.modules.otp import OTPConfiguration, OTPEnrollmentPublicDetails, OTPEnrollmentPrivateDetails, \
    OTPDeviceHandlerEnrollmentCompletion
from enrollment.models import Enrollment
from tenants.models import Tenant, Integration


class BaseEnrollmentTestCase(TestCase):
    TEST_INTEGRATION_NAME = 'Test Integration'

    def setUp(self):
        Tenant.create(
            name='Test Tenant',
            first_name='John',
            last_name='Doe',
            email='john.doe@email.com',
            password='john.doe')

        Integration.create(
            tenant=Tenant.objects.filter(name='Test Tenant').first(),
            name=BaseEnrollmentTestCase.TEST_INTEGRATION_NAME,
            notes='Test Notes')


class EnrollmentTestCase(BaseEnrollmentTestCase):
    TEST_USERNAME = 'test'

    def setUp(self):
        super(EnrollmentTestCase, self).setUp()

        DeviceKind.objects.create(
            name='OTP',
            module='devices.modules.otp.OTPDeviceKindModule',
            description='OTP Devices',
            configuration={
                'issuer_name': 'pymfa',
                'digits': 6,
                'algorithm': OTPConfiguration.ALGORITHM_SHA1,
                'secret_length': 32,
                'valid_window': 1,
                'interval': 30,
            })

        Module.objects.create(
            name='contrib.communications.DjangoSMTPMailer', configuration={})

        DeviceKind.objects.create(
            name='Email',
            module='devices.modules.email.EmailDeviceKindModule',
            description='Email Devices',
            configuration={
                'from_email': 'isaac@odemgroup.com',
                'subject': 'Your 2fa access token',
                'message': 'Your 2fa access token is `{token}`',
                'html_message': 'Your 2fa access token is `{token}`',
                'communication_module':
                'contrib.communications.DjangoSMTPMailer',
                'communication_module_settings': {},
            })

        e = Enrollment()

        e.integration = Integration.objects.filter(
            name=BaseEnrollmentTestCase.TEST_INTEGRATION_NAME).first()

        e.policy = e.integration.policy
        e.username = EnrollmentTestCase.TEST_USERNAME
        e.expires_at = timezone.now() + datetime.timedelta(minutes=10)

        e.save()

    def test_can_complete_email_enrollment(self):
        e = Enrollment.objects.get(username=EnrollmentTestCase.TEST_USERNAME)

        prep_data = EmailDeviceHandlerEnrollmentPreparation(
            data={'address': 'script3r@gmail.com'})

        self.assertTrue(prep_data.is_valid())

        ok, err = e.select_device(
            DeviceKind.objects.filter(name='Email').first(),
            prep_data.validated_data)

        self.assertIsNone(err)
        self.assertTrue(ok)

        private_details = EmailDevicePrivateEnrollmentDetails(
            data=e.private_details)
        self.assertTrue(private_details.is_valid())

    def test_can_complete_totp_enrollment(self):
        e = Enrollment.objects.get(username=EnrollmentTestCase.TEST_USERNAME)

        success, err = e.select_device(
            DeviceKind.objects.filter(name='OTP').first())

        self.assertIsNone(err)
        self.assertTrue(success)

        public_details = OTPEnrollmentPublicDetails(data=e.public_details)

        self.assertTrue(public_details.is_valid())
        self.assertTrue(public_details.validated_data['provisioning_uri']
                        .startswith('otpauth://'))

        private_details = OTPEnrollmentPrivateDetails(data=e.private_details)
        self.assertTrue(private_details.is_valid())

        totp = pyotp.TOTP(
            s=private_details.validated_data['secret'],
            interval=private_details.validated_data['interval'],
            digits=private_details.validated_data['digits'])

        self.assertTrue(e.status == Enrollment.STATUS_IN_PROGRESS)

        completion = OTPDeviceHandlerEnrollmentCompletion(
            data={'token': totp.now()})

        self.assertTrue(completion.is_valid())
        ok, err = e.complete(completion.validated_data)

        self.assertIsNone(err)
        self.assertTrue(ok)
