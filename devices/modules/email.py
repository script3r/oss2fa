from __future__ import unicode_literals

import datetime
import logging
import string

from django.core.mail import send_mail
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework import serializers

from challenge.models import Challenge
from core import errors
from devices.models import Device
from enrollment.models import Enrollment
from policy.models import Configuration
from verification.models import Verification
from .base import DeviceHandler

logger = logging.getLogger(__name__)


class EmailDeviceHandlerEnrollmentCompletion(serializers.Serializer):
    verification_pk = serializers.IntegerField()


class EmailDeviceChallengeCompletion(serializers.Serializer):
    token = serializers.CharField()


class EmailDeviceDetails(serializers.Serializer):
    address = serializers.EmailField()


class EmailDevicePrivateChallengeDetails(serializers.Serializer):
    token = serializers.CharField()


class EmailDeviceConfigurationModel(serializers.Serializer):
    pass


class EmailDeviceHandler(DeviceHandler):
    @staticmethod
    def mask_address(value):
        return value.split('@', 1)[1].lower()

    def get_configuration_model(self, data):
        return DeviceHandler.build_serializer_model(EmailDeviceConfigurationModel, data)

    def get_device_details_model(self, data):
        return DeviceHandler.build_serializer_model(EmailDeviceDetails, data)

    def get_enrollment_completion_model(self, data):
        return DeviceHandler.build_serializer_model(EmailDeviceHandlerEnrollmentCompletion, data)

    def get_challenge_completion_model(self, data):
        return DeviceHandler.build_serializer_model(EmailDeviceChallengeCompletion, data)

    def get_enrollment_public_details(self, data):
        return None

    def get_enrollment_private_details(self, data):
        return None

    def enrollment_prepare(self, enrollment):
        logger.info('preparing enrollment `{0}` for email processing'.format(
            enrollment))
        enrollment.status = Enrollment.STATUS_IN_PROGRESS

    def enrollment_complete(self, enrollment, data):
        with transaction.atomic():

            assert enrollment.status == Enrollment.STATUS_IN_PROGRESS
            assert not enrollment.is_expired()

            # mark the enrollment as failed
            enrollment.status = Enrollment.STATUS_FAILED

            # attempt to find matching verification
            verification = Verification.objects.filter(
                integration=enrollment.integration,
                delivery_method=Verification.DELIVERY_METHOD_EMAIL,
                pk=data['verification_pk']
            ).first()

            # if we cannot find, fail the enrollment
            if not verification:
                return False, errors.MFAMissingInformationError(
                    u'could not find email verification matching `{0}` for integration `{1}`', data['verification_pk'],
                    enrollment.integration)

            # make sure the verification is complete
            if verification.status != Verification.STATUS_COMPLETE:
                return False, errors.MFAInconsistentStateError(
                    u'verification status is set to `{0}` but expected `{1}`', verification.status,
                    Verification.STATUS_COMPLETE)

            # make sure it has not been consumed before
            if verification.consumed_at:
                return False, errors.MFAInconsistentStateError(u'verification `{0}` has been consumed at `{0}`',
                                                               verification.pk, verification.consumed_at)

            # mark the enrollment as complete
            enrollment.status = Enrollment.STATUS_COMPLETE

            # consume the verification
            verification.consumed_at = datetime.datetime.utcnow()

            # extract the device details
            details = EmailDeviceDetails(data={
                'address': verification.destination
            })

            if not details.is_valid():
                return False, errors.MFAMissingInformationError(u'could not validate email device details: {0}',
                                                                details.errors)

            # create the device
            device = Device()
            device.name = u'Email [@{0}]'.format(EmailDeviceHandler.mask_address(verification.destination))
            device.kind = enrollment.device_selection.kind
            device.enrollment = enrollment

            # save the device details
            device.details = details.validated_data

            # save the verification
            verification.save()

            return device, None

    def challenge_create(self, challenge):
        # make sure we are processing challenges in the right state.
        assert challenge.status == Challenge.STATUS_NEW

        # obtain the token length
        tk_len = challenge.policy.get_configuration(
            Configuration.KIND_CHALLENGE_TOKEN_LENGTH) or Challenge.DEFAULT_TOKEN_LENGTH

        # generate the security token
        token = get_random_string(length=tk_len, allowed_chars=string.digits)

        private_details = EmailDevicePrivateChallengeDetails(data={
            'token': token
        })

        if not private_details.is_valid():
            return False, errors.MFAMissingInformationError(u'could not validate email private details: {0}',
                                                            private_details.errors)

        # obtain the device information
        device, error = challenge.device.get_model()
        if error:
            logger.error('failed to obtain device model: {0}'.format(error))
            return False, error

        logger.info('sending challenge with token `{0}` to email `{1}`'.format(token, device['address']))

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
        serializer = EmailDevicePrivateChallengeDetails(data=challenge.private_details)
        if not serializer.is_valid():
            return False, errors.MFAMissingInformationError(serializer.errors)

        details = serializer.validated_data

        # compare the tokens
        if details['token'] != data['token']:
            logger.error('token `{0}` is not valid for challenge `{1}`'.format(data['token'], challenge.pk))
            return False, None

        return True, None
