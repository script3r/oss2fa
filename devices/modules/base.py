from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from core import errors


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
