from __future__ import unicode_literals

import string
from abc import ABCMeta, abstractmethod

from django.utils.crypto import get_random_string

from core import errors
from policy.models import Configuration


class DeviceKindModule(object):
    __metaclass__ = ABCMeta

    def __init__(self, configuration):
        self._configuration, err = self.get_configuration_model(configuration)
        if err:
            raise Exception(
                'could not instantiate configuration: {0}'.format(err))

    @staticmethod
    def build_model_instance(klass, data):
        instance = klass(data=data or {})
        if not instance.is_valid():
            return None, errors.MFAError(','.join(instance.errors))
        return instance.validated_data, None

    @staticmethod
    def generate_secure_token(policy):
        token_len = policy.get_configuration(
            Configuration.KIND_TOKEN_LENGTH) or Configuration.DEFAULT_TOKEN_LENGTH

        return get_random_string(length=token_len, allowed_chars=string.digits)

    @abstractmethod
    def get_configuration_model(self, data):
        pass

    @abstractmethod
    def get_device_details_model(self, data):
        pass

    @abstractmethod
    def get_enrollment_completion_model(self, data):
        pass

    @abstractmethod
    def get_challenge_completion_model(self, data):
        pass

    @abstractmethod
    def get_enrollment_prepare_model(self, data):
        pass

    @abstractmethod
    def get_enrollment_public_details_model(self, data):
        pass

    @abstractmethod
    def get_enrollment_private_details_model(self, data):
        pass

    @abstractmethod
    def enrollment_prepare(self, enrollment):
        pass

    @abstractmethod
    def enrollment_complete(self, enrollment, details):
        pass

    @abstractmethod
    def challenge_create(self, challenge):
        pass

    @abstractmethod
    def challenge_complete(self, challenge, details):
        pass
