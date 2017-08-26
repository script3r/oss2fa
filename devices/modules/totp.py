from __future__ import unicode_literals

import logging

import pyotp
from django.db import transaction
from rest_framework import serializers

from core import errors
from devices.models import Device
from enrollment.models import Enrollment
from .base import DeviceHandler

logger = logging.getLogger(__name__)


class TOTPConfiguration(serializers.Serializer):
    ALGORITHM_SHA1 = 'sha1'
    ALGORITHM_SHA256 = 'sha256'

    ALGORITHM_CHOICES = (
        (ALGORITHM_SHA1, 'sha1'),
        (ALGORITHM_SHA256, 'sha256'),
    )

    issuer_name = serializers.CharField(initial='Auth2')
    digits = serializers.IntegerField(initial=6)
    period = serializers.IntegerField(initial=30)
    algorithm = serializers.ChoiceField(choices=ALGORITHM_CHOICES, initial=ALGORITHM_SHA1)
    secret_length = serializers.IntegerField(initial=32)
    valid_window = serializers.IntegerField(initial=1)


class TOTPDeviceHandlerEnrollmentCompletion(serializers.Serializer):
    token = serializers.CharField()


class TOTPEnrollmentPrivateDetails(serializers.Serializer):
    issuer_name = serializers.CharField(initial='Auth2')
    digits = serializers.IntegerField(initial=6)
    period = serializers.IntegerField(initial=30)
    algorithm = serializers.ChoiceField(choices=TOTPConfiguration.ALGORITHM_CHOICES,
                                        initial=TOTPConfiguration.ALGORITHM_SHA1)
    secret = serializers.CharField()
    valid_window = serializers.IntegerField(initial=1)


class TOTPEnrollmentPublicDetails(serializers.Serializer):
    provisioning_uri = serializers.CharField()


class TOTPDeviceChallengeCompletion(serializers.Serializer):
    token = serializers.CharField()


class TOTPDeviceDetails(serializers.Serializer):
    issuer_name = serializers.CharField(initial='Auth2')
    digits = serializers.IntegerField(initial=6)
    period = serializers.IntegerField(initial=30)
    algorithm = serializers.ChoiceField(choices=TOTPConfiguration.ALGORITHM_CHOICES,
                                        initial=TOTPConfiguration.ALGORITHM_SHA1)
    secret = serializers.CharField()
    valid_window = serializers.IntegerField(initial=1)


class TOTPDevicePrivateChallengeDetails(serializers.Serializer):
    token = serializers.CharField()


class TOTPDeviceHandler(DeviceHandler):
    def get_configuration_model(self, data):
        return DeviceHandler.build_serializer_model(TOTPConfiguration, data)

    def get_device_details_model(self, data):
        return DeviceHandler.build_serializer_model(TOTPDeviceDetails, data)

    def get_enrollment_completion_model(self, data):
        return DeviceHandler.build_serializer_model(TOTPDeviceHandlerEnrollmentCompletion, data)

    def get_challenge_completion_model(self, data):
        return DeviceHandler.build_serializer_model(TOTPDeviceChallengeCompletion, data)

    def get_enrollment_public_details(self, data):
        return DeviceHandler.build_serializer_model(TOTPEnrollmentPublicDetails, data)

    def get_enrollment_private_details(self, data):
        return DeviceHandler.build_serializer_model(TOTPEnrollmentPrivateDetails, data)

    def enrollment_prepare(self, enrollment):
        assert enrollment.status == Enrollment.STATUS_NEW

        logger.info('preparing enrollment `{0}` for TOTP processing'.format(enrollment.pk))

        # create the secret for this session
        secret = pyotp.random_base32(length=self._configuration['secret_length'])

        # create the provisioning uri
        totp = pyotp.TOTP(
            s=secret,
            digits=self._configuration['digits'],
            interval=self._configuration['period']
        )

        # obtain the provisioning uri
        prov_uri = totp.provisioning_uri(enrollment.username, self._configuration['issuer_name'])

        # store the private details
        private_details, err = self.get_enrollment_private_details({
            'secret': secret,
            'issuer_name': self._configuration['issuer_name'],
            'digits': self._configuration['digits'],
            'period': self._configuration['period'],
            'algorithm': self._configuration['algorithm'],
            'valid_window': self._configuration['valid_window'],
            'provisioning_uri': prov_uri
        })

        if err:
            logger.error('failed to create enrollment private details: {0}'.format(err))
            return False, err

        # store the public details
        public_details, err = self.get_enrollment_public_details({
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

            private_details, err = self.get_enrollment_private_details(enrollment.private_details)
            if err:
                logger.error(
                    'failed to retrieve private details for TOTP enrollment `{0}`: {1}'.format(enrollment.pk, err))
                return False, err

            # create the provisioning uri
            totp = pyotp.TOTP(
                s=private_details['secret'],
                digits=private_details['digits'],
                interval=private_details['period']
            )

            ok = totp.verify(data['token'], valid_window=self._configuration['valid_window'])
            if not ok:
                logger.error(
                    'failed to verify TOTP `{0}` as valid for enrollment `{1}`'.format(data['token'], enrollment.pk))
                return False, errors.MFASecurityError(
                    'token mismatch: `{0}` is not a valid TOTP token for enrollment `{1}`'.format(data['token'],
                                                                                                  enrollment.pk))

            # extract the device details
            details = TOTPDeviceDetails(data={
                'issuer_name': private_details['issuer_name'],
                'digits': private_details['digits'],
                'period': private_details['period'],
                'secret': private_details['secret'],
                'valid_window': private_details['valid_window'],
                'algorithm': private_details['algorithm']
            })

            if not details.is_valid():
                logger.info('could not validate totp device details: {0}'.format(details.errors))

            # create the device
            device = Device()
            device.name = 'TOTP [{0}]'.format(enrollment.username)
            device.kind = enrollment.device_selection.kind
            device.enrollment = enrollment

            # save the device details
            device.details = details.validated_data

            return device, None

    def challenge_create(self, challenge):
        assert challenge.status == challenge.STATUS_NEW

        logger.info('creating TOTP challenge for `{0}`'.format(challenge.pk))
        return True, None

    def challenge_complete(self, challenge, data):
        assert challenge.status == challenge.STATUS_IN_PROGRESS

        logger.info('completing TOTP challenge `{0}` with `{1}`'.format(challenge.pk, data))

        # obtain the device module, and create the TOTP entity
        device = challenge.device.get_model()

        totp = pyotp.TOTP(
            s=device['secret'],
            digits=device['digits'],
            interval=device['period']
        )

        # verify the token given the validity window it was registered
        return totp.verify(data['token'], valid_window=self._configuration['valid_window']), None
