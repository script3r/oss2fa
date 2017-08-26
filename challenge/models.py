from __future__ import unicode_literals

import logging

from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from core import errors
from core.models import Entity
from policy.models import Policy
from tenants.models import Client, BindingContext

logger = logging.getLogger(__name__)


class Challenge(Entity):
    STATUS_NEW = 1
    STATUS_IN_PROGRESS = 2
    STATUS_COMPLETE = 3
    STATUS_FAILED = 4
    STATUS_EXPIRED = 5

    DEFAULT_TOKEN_LENGTH = 5
    DEFAULT_EXPIRATION_IN_MINUTES = 5

    STATUS_CHOICES = (
        (STATUS_NEW, _('New')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETE, _('Complete')),
        (STATUS_FAILED, _('Failed')),
        (STATUS_EXPIRED, _('Expired')),
    )

    client = models.ForeignKey(Client, related_name='challenges')
    device = models.ForeignKey('devices.Device', related_name='challenges')
    policy = models.ForeignKey(Policy, related_name='challenges')
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)
    binding_context = models.OneToOneField(
        BindingContext, related_name='challenge', blank=True, null=True)
    private_details = JSONField(blank=True, null=True)
    public_details = JSONField(blank=True, null=True)
    reference = models.CharField(max_length=128, blank=True, null=True)
    expires_at = models.DateTimeField()
    portal_url = models.URLField(blank=True, null=True)

    def is_expired(self):
        return self.expires_at < timezone.now()

    @staticmethod
    def get_by_integration_and_pk(pk, integration, **kwargs):
        return Challenge.objects.filter(pk=pk, client__integration=integration, **kwargs).first()

    def complete(self, payload):
        if self.status != Challenge.STATUS_IN_PROGRESS:
            return False, errors.MFAInconsistentStateError(
                'challenge `{0}` is in state `{1}` and cannot be completed', self.pk, self.get_status_display())

        if self.is_expired():
            return False, errors.MFAInconsistentStateError('challenge `{0}` expired at `{1}`', self.pk, self.expires_at)

        logger.info(
            'completing challenge `{0}` with `{1}`'.format(self.pk, payload))

        with transaction.atomic():
            assert self.status == Challenge.STATUS_IN_PROGRESS

            # obtain the device module
            module = self.device.kind.get_module()

            # get the completion model
            model, err = module.get_challenge_completion_model(payload)
            if err:
                logger.error(
                    'failed to get challenge completion model: {0}'.format(err))

                self.status = Challenge.STATUS_FAILED
                self.save()

                return False, err

            # complete the challenge
            success, err = module.challenge_complete(self, model)
            if err:
                logger.error(
                    'failed to complete challenge `{0}`: {1}'.format(self.pk, err))

                self.status = Challenge.STATUS_FAILED
                self.save()

                return False, err

            # if we are here, no errors.
            self.status = Challenge.STATUS_COMPLETE if success else Challenge.STATUS_FAILED
            self.save()

            return success, None
