from __future__ import unicode_literals

import logging

import pyotp
from django.db import transaction
from rest_framework import serializers

from core import errors
from devices.models import Device
from enrollment.models import Enrollment
from .base import DeviceKindModule

logger = logging.getLogger(__name__)


class OTPConfiguration(serializers.Serializer):
    ALGORITHM_SHA1 = 'sha1'
    ALGORITHM_SHA256 = 'sha256'

    ALGORITHM_CHOICES = (
        (ALGORITHM_SHA1, 'sha1'),
        (ALGORITHM_SHA256, 'sha256'),
    )

    issuer_name = serializers.CharField(initial='pymfa')
    digits = serializers.IntegerField(initial=6)
    interval = serializers.IntegerField(initial=30)
    algorithm = serializers.ChoiceField(choices=ALGORITHM_CHOICES, initial=ALGORITHM_SHA1)
    secret_length = serializers.IntegerField(initial=32)
    valid_window = serializers.IntegerField(initial=1)


class OTPDeviceHandlerEnrollmentCompletion(serializers.Serializer):
    token = serializers.CharField()


class OTPDeviceHandlerEnrollmentPreparation(serializers.Serializer):
    pass


class OTPEnrollmentPrivateDetails(serializers.Serializer):
    issuer_name = serializers.CharField(initial='Auth2')
    digits = serializers.IntegerField(initial=6)
    interval = serializers.IntegerField(initial=30)
    algorithm = serializers.ChoiceField(choices=OTPConfiguration.ALGORITHM_CHOICES,
                                        initial=OTPConfiguration.ALGORITHM_SHA1)
    secret = serializers.CharField()
    valid_window = serializers.IntegerField(initial=1)


class OTPEnrollmentPublicDetails(serializers.Serializer):
    provisioning_uri = serializers.CharField()


class OTPDeviceChallengeCompletion(serializers.Serializer):
    token = serializers.CharField()


class OTPDeviceDetails(serializers.Serializer):
    issuer_name = serializers.CharField(initial='Auth2')
    digits = serializers.IntegerField(initial=6)
    interval = serializers.IntegerField(initial=30)
    algorithm = serializers.ChoiceField(choices=OTPConfiguration.ALGORITHM_CHOICES,
                                        initial=OTPConfiguration.ALGORITHM_SHA1)
    secret = serializers.CharField()
    valid_window = serializers.IntegerField(initial=1)


class OTPDevicePrivateChallengeDetails(serializers.Serializer):
    token = serializers.CharField()


class OTPDeviceKindModule(DeviceKindModule):
    def get_configuration_model(self, data):
        return DeviceKindModule.build_model_instance(OTPConfiguration, data)

    def get_device_details_model(self, data):
        return DeviceKindModule.build_model_instance(OTPDeviceDetails, data)

    def get_enrollment_prepare_model(self, data):
        return DeviceKindModule.build_model_instance(OTPDeviceHandlerEnrollmentPreparation, data)

    def get_enrollment_completion_model(self, data):
        return DeviceKindModule.build_model_instance(OTPDeviceHandlerEnrollmentCompletion, data)

    def get_challenge_completion_model(self, data):
        return DeviceKindModule.build_model_instance(OTPDeviceChallengeCompletion, data)

    def get_enrollment_public_details_model(self, data):
        return DeviceKindModule.build_model_instance(OTPEnrollmentPublicDetails, data)

    def get_enrollment_private_details_model(self, data):
        return DeviceKindModule.build_model_instance(OTPEnrollmentPrivateDetails, data)

    def enrollment_prepare(self, enrollment):
        assert enrollment.status == Enrollment.STATUS_NEW

        logger.info('preparing enrollment `{0}` for OTP processing'.format(enrollment.pk))

        # create the secret for this session
        secret = pyotp.random_base32(length=self._configuration['secret_length'])

        # create the provisioning uri
        OTP = pyotp.TOTP(
            s=secret,
            digits=self._configuration['digits'],
            interval=self._configuration['interval']
        )

        # obtain the provisioning uri
        prov_uri = OTP.provisioning_uri(enrollment.username, self._configuration['issuer_name'])

        # store the private details
        private_details, err = self.get_enrollment_private_details_model({
            'secret': secret,
            'issuer_name': self._configuration['issuer_name'],
            'digits': self._configuration['digits'],
            'interval': self._configuration['interval'],
            'algorithm': self._configuration['algorithm'],
            'valid_window': self._configuration['valid_window'],
            'provisioning_uri': prov_uri
        })

        if err:
            logger.error('failed to create enrollment private details: {0}'.format(err))
            return False, err

        # store the public details
        public_details, err = self.get_enrollment_public_details_model({
            'provisioning_uri': prov_uri
        })

        if err:
            logger.error('failed to create enrollment public details: {0}'.format(err))
            return False, err

        enrollment.private_details = dict(private_details)
        enrollment.public_details = dict(public_details)

        return True, None

    def enrollment_complete(self, enrollment, data):
        with transaction.atomic():
            assert enrollment.status == Enrollment.STATUS_IN_PROGRESS
            assert not enrollment.is_expired()

            # mark the enrollment as failed
            enrollment.status = Enrollment.STATUS_FAILED

            private_details, err = self.get_enrollment_private_details_model(enrollment.private_details)
            if err:
                logger.error(
                    'failed to retrieve private details for OTP enrollment `{0}`: {1}'.format(enrollment.pk, err))
                return False, err

            # create the provisioning uri
            OTP = pyotp.TOTP(
                s=private_details['secret'],
                digits=private_details['digits'],
                interval=private_details['interval']
            )

            ok = OTP.verify(data['token'], valid_window=self._configuration['valid_window'])
            if not ok:
                logger.error(
                    'failed to verify OTP `{0}` as valid for enrollment `{1}`'.format(data['token'], enrollment.pk))
                return False, errors.MFASecurityError(
                    'token mismatch: `{0}` is not a valid OTP token for enrollment `{1}`'.format(data['token'],
                                                                                                 enrollment.pk))

            # extract the device details
            details = OTPDeviceDetails(data={
                'issuer_name': private_details['issuer_name'],
                'digits': private_details['digits'],
                'interval': private_details['interval'],
                'secret': private_details['secret'],
                'valid_window': private_details['valid_window'],
                'algorithm': private_details['algorithm']
            })

            if not details.is_valid():
                logger.info('could not validate OTP device details: {0}'.format(details.errors))

            # create the device
            device = Device()
            device.name = 'OTP [{0}]'.format(enrollment.username)
            device.kind = enrollment.device_selection.kind
            device.enrollment = enrollment

            # save the device details
            device.details = details.validated_data

            return device, None

    def challenge_create(self, challenge):
        assert challenge.status == challenge.STATUS_NEW

        logger.info('creating OTP challenge for `{0}`'.format(challenge.pk))
        return True, None

    def challenge_complete(self, challenge, data):
        assert challenge.status == challenge.STATUS_IN_PROGRESS

        logger.info('completing OTP challenge `{0}` with `{1}`'.format(challenge.pk, data))

        # obtain the device module, and create the OTP entity
        device = challenge.device.get_model()

        OTP = pyotp.OTP(
            s=device['secret'],
            digits=device['digits'],
            interval=device['interval']
        )

        # verify the token given the validity window it was registered
        return OTP.verify(data['token'], valid_window=self._configuration['valid_window']), None
