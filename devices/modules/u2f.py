from __future__ import unicode_literals

import logging
import string

from django.core.mail import send_mail
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework import serializers
from u2flib_server import u2f

from challenge.models import Challenge
from core import errors
from devices.models import Device
from enrollment.models import Enrollment
from policy.models import Configuration
from .base import DeviceHandler

logger = logging.getLogger(__name__)


class U2FDeviceHandlerEnrollmentCompletion(serializers.Serializer):
    registration_response = serializers.JSONField()


class U2FDeviceChallengeCompletion(serializers.Serializer):
    token = serializers.CharField()


class U2FDeviceDetails(serializers.Serializer):
    public_key = serializers.CharField()
    key_handle = serializers.CharField()
    app_id = serializers.CharField()


class U2FDevicePrivateChallengeDetails(serializers.Serializer):
    token = serializers.CharField()


class U2FEnrollmentPublicDetails(serializers.Serializer):
    registration_request = serializers.JSONField()


class U2FDeviceConfigurationModel(serializers.Serializer):
    pass


class U2FDeviceHandler(DeviceHandler):
    def get_u2f_devices_from_enrollment(self, enrollment):
        result = []
        if not enrollment.client:
            return result

        for device in enrollment.client.devices.all():
            if device.kind.name == 'U2F':
                result.append(self.get_device_details_model(device.details))
        return result

    def get_configuration_model(self, data):
        return DeviceHandler.build_serializer_model(U2FDeviceConfigurationModel, data)

    def get_device_details_model(self, data):
        return DeviceHandler.build_serializer_model(U2FDeviceDetails, data)

    def get_enrollment_completion_model(self, data):
        return DeviceHandler.build_serializer_model(U2FDeviceHandlerEnrollmentCompletion, data)

    def get_challenge_completion_model(self, data):
        return DeviceHandler.build_serializer_model(U2FDeviceChallengeCompletion, data)

    def get_enrollment_public_details(self, data):
        return DeviceHandler.build_serializer_model(U2FEnrollmentPublicDetails, data)

    def get_enrollment_private_details(self, data):
        return None

    def enrollment_prepare(self, enrollment):
        logger.info('preparing enrollment `{0}` for U2F processing'.format(enrollment))

        registration_request = u2f.start_register(
            app_id=enrollment.integration.endpoint,
            devices=self.get_u2f_devices_from_enrollment(enrollment)
        )

        # store the public details
        public_details, err = self.get_enrollment_public_details({
            'registration_request': registration_request.json
        })

        if err:
            logger.error('failed to create u2f challenge: {0}'.format(err))
            return False, err

        enrollment.public_details = public_details
        return True, None

    def enrollment_complete(self, enrollment, data):
        with transaction.atomic():

            assert enrollment.status == Enrollment.STATUS_IN_PROGRESS
            assert not enrollment.is_expired()

            # mark the enrollment as failed
            enrollment.status = Enrollment.STATUS_FAILED

            public_details, err = self.get_enrollment_public_details(enrollment.public_details)
            if err:
                logger.error('could not obtain u2f registration request: {0}'.format(err))
                return False, err

            enrollment_completion, err = self.get_enrollment_completion_model(data)
            if err:
                logger.error('could not obtain u2f enrollment completion data: {0}'.format(err))
                return False, err

            binding, cert = u2f.complete_register(
                public_details['registration_request'],
                enrollment_completion['registration_response'],
                [enrollment.integration.endpoint]
            )

            # mark the enrollment as complete
            enrollment.status = Enrollment.STATUS_COMPLETE

            # create the device
            device = Device()
            device.name = 'U2F Token'
            device.kind = enrollment.device_selection.kind
            device.enrollment = enrollment

            # extract the device details
            details, err = self.get_device_details_model(data={
                'public_key': binding['publicKey'],
                'key_handle': binding['keyHandle'],
                'app_id': binding['appId']
            })

            if err:
                logger.error('could not build u2f device model: {0}'.format(err))
                return False, err

            # save the device details
            device.details = details

            return device, None

    def challenge_create(self, challenge):
        # make sure we are processing challenges in the right state.
        assert challenge.status == Challenge.STATUS_NEW

        # obtain the token length
        tk_len = challenge.policy.get_configuration(
            Configuration.KIND_CHALLENGE_TOKEN_LENGTH) or Challenge.DEFAULT_TOKEN_LENGTH

        # generate the security token
        token = get_random_string(length=tk_len, allowed_chars=string.digits)

        private_details = U2FDevicePrivateChallengeDetails(data={
            'token': token
        })

        if not private_details.is_valid():
            return False, errors.MFAMissingInformationError(u'could not validate U2F private details: {0}',
                                                            private_details.errors)

        # obtain the device information
        device, error = challenge.device.get_model()
        if error:
            logger.error('failed to obtain device model: {0}'.format(error))
            return False, error

        logger.info('sending challenge with token `{0}` to U2F `{1}`'.format(token, device['address']))

        # send the e-mail challenge
        send_mail(
            'Your Challenge Token is `{0}`'.format(token),
            'Your Challenge Token is `{0}`'.format(token),
            'security@rnkr.io',
            [device['address']]
        )

        challenge.private_details = private_details.validated_data
        return True, None

    def challenge_complete(self, challenge, data):
        assert challenge.status == Challenge.STATUS_IN_PROGRESS

        # get the private challenge details; fail if we can't validate
        serializer = U2FDevicePrivateChallengeDetails(data=challenge.private_details)
        if not serializer.is_valid():
            return False, errors.MFAMissingInformationError(serializer.errors)

        details = serializer.validated_data

        # compare the tokens
        if details['token'] != data['token']:
            logger.error('token `{0}` is not valid for challenge `{1}`'.format(data['token'], challenge.pk))
            return False, None

        return True, None
