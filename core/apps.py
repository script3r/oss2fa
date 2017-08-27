from __future__ import unicode_literals

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    did_load = False

    def ready(self):
        if not self.did_load:
            self.did_load = True
