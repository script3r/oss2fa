from django.test import TestCase

from .models import Tenant, Integration


class IntegrationTestCase(TestCase):
    def setUp(self):
        Tenant.create(
            name='Test Tenant',
            first_name='John',
            last_name='Doe',
            email='john.doe@email.com',
            password='john.doe'
        )

    def test_can_create_integration(self):
        integration = Integration.create(
            tenant=Tenant.objects.filter(name='Test Tenant').first(),
            name='Test Integration',
            notes='Test Notes'
        )

        self.assertIsNotNone(integration.access_key)
        self.assertIsNotNone(integration.secret_key)
