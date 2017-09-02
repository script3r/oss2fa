from __future__ import unicode_literals

import uuid
from datetime import timedelta

from django.apps import apps
from django.contrib.auth.models import User, Group
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from encrypted_fields import EncryptedCharField

from core import errors
from core.models import Entity
from policy.models import Policy, Configuration


class Tenant(Entity):
    DEFAULT_TENANT_NAME = 'Default'

    class Meta:
        unique_together = ('name', )

    @staticmethod
    def create(name, email, password, first_name='', last_name=''):
        with transaction.atomic():
            # create the tenant
            tenant = Tenant.objects.create(name=name)

            # create initial tenant user
            tenant_user = TenantUser.create(
                tenant=tenant,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name)

            # create all initial groups
            initial_groups = TenantGroup.create_initial_tenant_groups(tenant)

            # add tenant user to all newly created groups
            for initial_group in initial_groups:
                tenant_user.add_to_tenant_group(initial_group)

            tenant_user.save()
            return tenant


class TenantGroup(models.Model):
    ADMIN_GROUP_NAME = _('Administrators For `{name}`')

    INITIAL_GROUPS = [ADMIN_GROUP_NAME]

    tenant = models.ForeignKey(
        Tenant, related_name='groups', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    group = models.OneToOneField(
        Group, related_name='tenant_group', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            'tenant',
            'name', )

    @staticmethod
    def create(tenant, name):
        group_name = name.format(name=tenant.name)
        return TenantGroup.objects.create(
            tenant=tenant,
            name=group_name,
            group=Group.objects.create(name=group_name))

    @staticmethod
    def create_initial_tenant_groups(tenant):
        return [
            TenantGroup.create(tenant, x) for x in TenantGroup.INITIAL_GROUPS
        ]


class TenantUser(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='tenant_user')
    tenant = models.ForeignKey(
        Tenant, related_name='users', on_delete=models.CASCADE)
    groups = models.ManyToManyField(TenantGroup, related_name='users')

    @staticmethod
    def create(tenant, email, password, first_name='', last_name=''):
        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name)

        user.set_password(password)
        user.save()

        return TenantUser.objects.create(tenant=tenant, user=user)

    def add_to_tenant_group(self, tenant_group):
        self.groups.add(tenant_group)
        self.user.groups.add(tenant_group.group)


class Integration(Entity):
    DEFAULT_INTEGRATION_NAME = 'Default'

    ACCESS_KEY_LENGTH = 32
    SECRET_KEY_LENGTH = 48

    tenant = models.ForeignKey(
        Tenant, related_name='integrations', on_delete=models.CASCADE)
    policy = models.OneToOneField(
        Policy, related_name='integration', on_delete=models.CASCADE)
    access_key = models.CharField(max_length=128, unique=True)
    secret_key = EncryptedCharField(max_length=128, unique=True)
    endpoint = models.URLField(blank=True)
    notes = models.TextField(blank=True, null=True)
    uid = models.CharField(max_length=16, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = uuid.uuid4().get_hex()[:8]
        super(Integration, self).save(*args, **kwargs)

    @staticmethod
    def create(tenant, name, notes):
        return Integration.objects.create(
            tenant=tenant,
            name=name,
            notes=notes,
            policy=Policy.objects.create(name=name),
            access_key=get_random_string(Integration.ACCESS_KEY_LENGTH),
            secret_key=get_random_string(Integration.SECRET_KEY_LENGTH), )

    def generate_auth_session_token(self, username, expires_at):
        return ''

    def generate_auth_session_portal_url(self, kind, username, expires_at):
        return self.endpoint + '/' + kind + '/?token=' + self.generate_auth_session_token(
            username, expires_at)

    def enroll(self, username):
        client = Client.objects.filter(
            integration=self, username=username).first()
        if client:
            return None, errors.MFAError('username `{0}` already exists',
                                         username)

        Enrollment = apps.get_model('enrollment', 'Enrollment')

        expiration_mins = self.policy.get_configuration(
            Configuration.KIND_ENROLLMENT_EXPIRATION_IN_MINUTES
        ) or Enrollment.DEFAULT_EXPIRATION_IN_MINUTES
        expires_at = timezone.now() + timedelta(minutes=expiration_mins)

        entity = Enrollment.objects.create(
            integration=self,
            policy=self.policy,
            username=username,
            binding_context=None,
            expires_at=expires_at,
            portal_url=self.generate_auth_session_portal_url(
                'enrollment', username, expires_at))

        return entity, None

    def challenge(self, client, data):
        assert client.integration == self

        Challenge = apps.get_model('challenge', 'Challenge')

        device = None
        if data['device_pk']:
            device = client.devices.filter(pk=data['device_pk']).first()
            if not device:
                return None, errors.MFAInconsistentStateError(
                    'device `{0}` does not exist for client `{1}`'.format(
                        data['device_pk'], client.username))

        # obtain the challenge expiration in minute
        expiration_mins = self.policy.get_configuration(
            Configuration.KIND_CHALLENGE_EXPIRATION_IN_MINUTES
        ) or Challenge.DEFAULT_EXPIRATION_IN_MINUTES

        expires_at = timezone.now() + timedelta(minutes=expiration_mins)

        # create the challenge entity
        entity = Challenge.objects.create(
            client=client,
            device=device,
            policy=self.policy,
            reference=data['reference'] if 'reference' in data else '',
            expires_at=expires_at,
            portal_url=self.generate_auth_session_portal_url(
                'challenge', client.username, expires_at))

        return entity, None


class ClientGroup(Entity):
    pass


class BindingContext(models.Model):
    client_ip_address = models.GenericIPAddressField(blank=True, null=True)
    client_browser_fingerprint = models.CharField(
        max_length=256, blank=True, null=True)


class Client(Entity):
    STATUS_ACTIVE = 1
    STATUS_BYPASS = 2
    STATUS_INACTIVE = 3

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_BYPASS, _('Bypass')),
        (STATUS_INACTIVE, _('Inactive')), )

    integration = models.ForeignKey(Integration, related_name='clients')
    group = models.ForeignKey(
        ClientGroup, related_name='groups', blank=True, null=True)
    username = models.CharField(max_length=64)
    email = models.EmailField(blank=True, null=True)
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    def __unicode__(self):
        return self.username

    class Meta:
        unique_together = ('integration', 'username')
