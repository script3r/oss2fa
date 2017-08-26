from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from encrypted_fields import EncryptedCharField

from core.models import Entity
from tenants.models import Integration


class Verification(Entity):
    STATUS_NEW = 1
    STATUS_IN_PROGRESS = 2
    STATUS_COMPLETE = 3
    STATUS_FAILED = 4
    STATUS_EXPIRED = 5

    STATUS_CHOICES = (
        (STATUS_NEW, _('New')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETE, _('Complete')),
        (STATUS_FAILED, _('Failed')),
        (STATUS_EXPIRED, _('Expired')),
    )

    DELIVERY_METHOD_SMS = 1
    DELIVERY_METHOD_VOICE = 2
    DELIVERY_METHOD_EMAIL = 3

    DELIVERY_METHOD_CHOICES = (
        (DELIVERY_METHOD_SMS, _('SMS')),
        (DELIVERY_METHOD_VOICE, _('Voice')),
        (DELIVERY_METHOD_EMAIL, _('E-Mail')),
    )

    integration = models.ForeignKey(Integration, related_name='verifications')
    delivery_method = models.PositiveSmallIntegerField(
        choices=DELIVERY_METHOD_CHOICES)
    token = EncryptedCharField(max_length=16, blank=True)
    expires_at = models.DateTimeField()
    destination = models.CharField(max_length=128)
    consumed_at = models.DateTimeField(blank=True, null=True)
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)
