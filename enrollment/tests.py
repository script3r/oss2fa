import datetime

import pyotp
import urlparse

from django.test import TestCase
from django.utils import timezone

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from contrib.models import Module
from devices.models import DeviceKind
from devices.modules.email import EmailDeviceEnrollmentPrivateDetails, EmailDeviceEnrollmentPrepareRequest, EmailDeviceEnrollmentCompleteRequest
from devices.modules.otp import OTPConfiguration, OTPEnrollmentPublicDetails, OTPEnrollmentPrivateDetails, \
    OTPDeviceHandlerEnrollmentCompletion
from enrollment.models import Enrollment
from tenants.models import Tenant, Integration

BASE_TEST_INTEGRATION_NAME = 'Test Integration'
BASE_TEST_USERNAME = 'test'


class BaseEnrollmentTestCase(TestCase):
    def setUp(self):
        Tenant.create(
            name='Test Tenant',
            first_name='John',
            last_name='Doe',
            email='john.doe@email.com',
            password='john.doe')

        Integration.create(
            tenant=Tenant.objects.filter(name='Test Tenant').first(),
            name=BASE_TEST_INTEGRATION_NAME,
            notes='Test Notes')

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


class EnrollmentModelTestCase(BaseEnrollmentTestCase):
    def setUp(self):
        super(EnrollmentModelTestCase, self).setUp()

        e = Enrollment()

        e.integration = Integration.objects.filter(
            name=BASE_TEST_INTEGRATION_NAME).first()

        e.policy = e.integration.policy
        e.username = BASE_TEST_USERNAME
        e.expires_at = timezone.now() + datetime.timedelta(minutes=10)

        e.save()

    def test_can_complete_email_enrollment(self):
        e = Enrollment.objects.get(username=BASE_TEST_USERNAME)

        prep_data = EmailDeviceEnrollmentPrepareRequest(
            data={'address': 'script3r@gmail.com'})

        self.assertTrue(prep_data.is_valid())

        err = e.prepare({
            'kind': DeviceKind.objects.get(name='Email'),
            'options': prep_data.validated_data
        })

        self.assertIsNone(err)

        private_details = EmailDeviceEnrollmentPrivateDetails(
            data=e.private_details)

        self.assertTrue(private_details.is_valid())

        completion_data = EmailDeviceEnrollmentCompleteRequest(data={
            'token': private_details.validated_data['token']
        })

        self.assertTrue(completion_data.is_valid())

        err = e.complete(completion_data.validated_data)
        self.assertIsNone(err)

    def test_can_complete_totp_enrollment(self):
        e = Enrollment.objects.get(username=BASE_TEST_USERNAME)

        err = e.prepare({
            'kind': DeviceKind.objects.get(name='OTP'),
            'options': None
        })

        self.assertIsNone(err)

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
        err = e.complete(completion.validated_data)

        self.assertIsNone(err)


class EnrollmentAPITestCase(BaseEnrollmentTestCase, APITestCase):
    def setUp(self):
        super(EnrollmentAPITestCase, self).setUp()

        self._integration = Integration.objects.get(name=BASE_TEST_INTEGRATION_NAME)
        self._additional_headers = {
            'X_INTEGRATION_TOKEN': self._integration.access_key
        }

    def test_create_and_complete_totp_enrollment(self):
        username = BASE_TEST_USERNAME + '_1'

        url = reverse('enrollment-list')
        data = {'username': username}

        res = self.client.post(url, data, format='json', headers=self._additional_headers)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Enrollment.objects.filter(username=username, integration=self._integration).count(), 1)

        doc = res.json()
        url = reverse('enrollment-detail-prepare-device', kwargs={'pk': doc['pk']})

        data = {
            'kind': DeviceKind.objects.get(name='OTP').pk,
            'options': {
                'generate_qr_code': True,
            }
        }

        res = self.client.post(url, data, format='json', headers=self._additional_headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        doc = res.json()
        self.assertTrue('provisioning_uri' in doc['public_details'])

        prov_uri_parts = urlparse.urlsplit(doc['public_details']['provisioning_uri'])
        secret = urlparse.parse_qs(prov_uri_parts.query)['secret'][0]

        totp = pyotp.TOTP(secret)

        data = {
            'token': totp.now()
        }

        url = reverse('enrollment-complete', kwargs={'pk': doc['pk']})
        res = self.client.post(url, data, format='json', headers=self._additional_headers)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

