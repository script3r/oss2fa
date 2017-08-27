# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import importlib

from django.contrib.postgres.fields import JSONField
from django.db import models


class Module(models.Model):
    name = models.CharField(max_length=128, unique=True)
    configuration = JSONField(blank=True, null=True)

    def get_instance(self):
        parts = self.name.rsplit('.', 1)
        klass = getattr(importlib.import_module(parts[0]), parts[1])
        return klass(self.configuration)
