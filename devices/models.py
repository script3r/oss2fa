from __future__ import unicode_literals

import importlib

from django.contrib.postgres.fields import JSONField
from django.db import models

from core.models import Entity


class DeviceKind(models.Model):
    name = models.CharField(max_length=128, unique=True)
    module = models.CharField(max_length=128)
    configuration = JSONField(blank=True, null=True)
    description = models.TextField()


    def get_module(self):
        parts = self.module.rsplit('.', 1)
        klass = getattr(importlib.import_module(parts[0]), parts[1])
        return klass(self.configuration)


class Device(Entity):
    kind = models.ForeignKey(DeviceKind, related_name='devices')
    client = models.ForeignKey('tenants.Client', related_name='devices')
    enrollment = models.ForeignKey('enrollment.Enrollment')
    details = JSONField()

    def get_model(self):
        return self.kind.get_module().get_device_details_model(self.details)

    class Meta:
        unique_together = ('name', 'client',)


class DeviceSelection(models.Model):
    kind = models.ForeignKey(DeviceKind, related_name='selections')
    options = JSONField(blank=True, null=True)

    def __unicode__(self):
        return self.kind.name
