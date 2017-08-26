from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import Entity


class Policy(Entity):
    def get_rule(self, kind):
        entry = self.rules.filter(kind=kind).first()
        if not entry:
            return None

        return entry.get_parsed_value()

    def get_configuration(self, kind):
        entry = self.configurations.filter(kind=kind).first()
        if not entry:
            return None

        return entry.get_parsed_value()


class Configuration(models.Model):
    KIND_CHALLENGE_TOKEN_LENGTH = 1
    KIND_CHALLENGE_EXPIRATION_IN_MINUTES = 2
    KIND_ENROLLMENT_EXPIRATION_IN_MINUTES = 3

    KIND_CHOICES = (
        (KIND_CHALLENGE_TOKEN_LENGTH, _('Challenge Token Length')),
        (KIND_CHALLENGE_EXPIRATION_IN_MINUTES, _('Challenge Expiration (Minutes)')),
        (KIND_ENROLLMENT_EXPIRATION_IN_MINUTES, _('Enrollment Expiration (Minutes)')),
    )

    KIND_PROCESSORS = {
        KIND_CHALLENGE_TOKEN_LENGTH: lambda x: int(float(x)),
        KIND_CHALLENGE_EXPIRATION_IN_MINUTES: lambda x: int(float(x)),
        KIND_ENROLLMENT_EXPIRATION_IN_MINUTES: lambda x: int(float(x))
    }

    policy = models.ForeignKey(Policy, related_name='configurations')
    kind = models.PositiveSmallIntegerField(choices=KIND_CHOICES)
    value = models.CharField(max_length=64)

    def get_parsed_value(self):
        if self.kind in Configuration.KIND_PROCESSORS:
            return Configuration.KIND_PROCESSORS[self.kind](self.value)
        return self.value

    class Meta:
        unique_together = ('policy', 'kind',)


class Rule(models.Model):
    KIND_DEVICE_SELECTION = 1
    KIND_EMAIL_DOMAIN_RESTRICTION = 2

    KIND_PROCESSORS = {
        KIND_DEVICE_SELECTION: lambda x: x['allowedDeviceKinds'],
        KIND_EMAIL_DOMAIN_RESTRICTION: lambda x: x['allowedDomains']
    }

    KIND_CHOICES = (
        (KIND_DEVICE_SELECTION, _('Device Selection Restriction')),
        (KIND_EMAIL_DOMAIN_RESTRICTION, _('E-mail Domain Restriction')),
    )

    policy = models.ForeignKey(Policy, related_name='rules')
    kind = models.PositiveSmallIntegerField(choices=KIND_CHOICES)
    definition = JSONField()

    def get_parsed_value(self):
        if self.kind in Rule.KIND_PROCESSORS:
            return Rule.KIND_PROCESSORS[self.kind](self.definition)
        return self.definition

    class Meta:
        unique_together = ('policy', 'kind',)
