from __future__ import unicode_literals

from django.db import models


class Entity(models.Model):
    name = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
