from __future__ import unicode_literals

import logging

from django.apps import apps
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from core import errors
from core.models import Entity
from policy.models import Policy, Rule
from tenants.models import Integration, Client, BindingContext

logger = logging.getLogger(__name__)


class Enrollment(Entity):
    STATUS_NEW = 1
    STATUS_IN_PROGRESS = 2
    STATUS_COMPLETE = 3
    STATUS_FAILED = 4
    STATUS_EXPIRED = 5

    DEFAULT_EXPIRATION_IN_MINUTES = 5

    STATUS_CHOICES = (
        (STATUS_NEW, _('New')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETE, _('Complete')),
        (STATUS_FAILED, _('Failed')),
        (STATUS_EXPIRED, _('Expired')),
    )

    integration = models.ForeignKey(Integration, related_name='enrollments')
    client = models.OneToOneField(
        Client, related_name='enrollment', blank=True, null=True)
    policy = models.ForeignKey(Policy, related_name='enrollments')
    device_selection = models.OneToOneField(
        'devices.DeviceSelection', related_name='enrollment', blank=True, null=True)
    username = models.CharField(max_length=64)
    binding_context = models.OneToOneField(
        BindingContext, related_name='enrollments', blank=True, null=True)
    expires_at = models.DateTimeField()
    private_details = JSONField(blank=True, null=True)
    public_details = JSONField(blank=True, null=True)
    portal_url = models.URLField(blank=True, null=True)

    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)

    @staticmethod
    def get_by_integration_and_pk(pk, integration, **kwargs):
        return Enrollment.objects.filter(pk=pk, client__integration=integration, **kwargs).first()

    def __validate_device_selection(self):
        allowed_devices = self.policy.get_rule(Rule.KIND_DEVICE_SELECTION)
        if not allowed_devices:
            return True

        if self.device_selection.kind.name not in allowed_devices:
            raise ValidationError(
                'device kind `{0}` is not in list of allowed devices: {1}'.format(self.device_selection.kind.name,
                                                                                  allowed_devices))

    def clean(self):
        # make sure we are not
        if self.client and self.status != Enrollment.STATUS_COMPLETE:
            raise ValidationError(
                'a client entity cannot be assigned to this enrollment unless it is marked as complete')

        self.__validate_device_selection()

    def is_expired(self):
        self.expires_at < timezone.now()

    def _fail_enrollment(self, cause=None):
        logger.error(
            u'failing enrollment `{0}` due to: {1}'.format(self.pk, cause))
        self.status = Enrollment.STATUS_FAILED
        self.save()

        return False, cause

    def prepare(self):
        with transaction.atomic():
            assert self.status == Enrollment.STATUS_NEW
            assert self.device_selection is not None

            logger.info(
                'processing enrollment preparation for `{0}`'.format(self.pk))

            # get the device module, and prepare enrollment
            _, err = self.device_selection.kind.get_module().enrollment_prepare(self)
            if err:
                logger.error('failed to prepare enrollment `{0}` for device kind `{1}`: {2}'.format(self.pk,
                                                                                                    self.device_selection.get_kind_display(),
                                                                                                    err))
                return False, err

            self.status = Enrollment.STATUS_IN_PROGRESS
            self.save()
            return True, None

    def select_device(self, selection):
        if self.device_selection:
            return None, errors.MFAError('enrollment `{0}` already has a device selection of kind `{1}`'.format(self.pk,
                                                                                                                self.device_selection.kind))

        with transaction.atomic():
            DeviceSelection = apps.get_model('devices', 'DeviceSelection')

            self.device_selection = DeviceSelection.objects.create(
                kind=selection['kind'],
                options=selection['options']
            )

            self.save()

            logger.info('preparing enrollment `{0}` for device election of kind `{1}`'.format(self.pk,
                                                                                              self.device_selection.kind))

            return self.prepare()

    def complete(self, payload):
        if self.status != Enrollment.STATUS_IN_PROGRESS:
            return False, errors.MFAInconsistentStateError('enrollment `{0}` is in state `{1}` and cannot be completed',
                                                           self.pk, self.get_status_display())

        with transaction.atomic():
            assert self.status == Enrollment.STATUS_IN_PROGRESS
            assert self.device_selection is not None

            logger.info('processing completion for enrollment `{0}` with `{1}`'.format(
                self.pk, payload))

            # get the device module
            device_module = self.device_selection.kind.get_module()

            # get the enrollment completion model
            completion, err = device_module.get_enrollment_completion_model(
                payload)

            # if we couldn't parse the data, fail
            if err:
                logger.error(
                    'failed to retrieve enrollment completion model: {0}'.format(err))
                return self._fail_enrollment(err)

            # attempt to complete the enrollment
            device, error = device_module.enrollment_complete(self, completion)

            # if we have an error, fail
            if error:
                return self._fail_enrollment(error)

            # create the client entity
            client = Client.objects.create(
                name=self.username,
                integration=self.integration,
                username=self.username
            )

            # update the device to reflect the client entity
            device.client = client
            device.save()

            # update the enrollment
            self.status = Enrollment.STATUS_COMPLETE
            self.client = client

            self.save()

            return True, None
