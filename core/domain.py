from abc import ABCMeta, abstractmethod

import boto3

from core import errors
from tenants.models import Integration


class IntegrationDNSMapper():
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_integration_endpoint(self, integration_pk):
        pass

    @abstractmethod
    def destroy_integration_endpoint(self, integration_pk):
        pass


class AmazonRoute53DNSMapper(IntegrationDNSMapper):
    def __init__(self, hosted_zone_id, root_domain, proxy_domain):
        self._hosted_zone_id = hosted_zone_id
        self._root_domain = root_domain
        self._proxy_domain = proxy_domain

    def _get_client(self):
        return boto3.client('route53')

    def _cname_record_action(self, action, integration):
        return self._get_client().change_resource_record_sets(
            HostedZoneId=self._hosted_zone_id,
            ChangeBatch={
                'Comment': 'comment',
                'Changes': [
                    {
                        'Action': action.upper(),
                        'ResourceRecordSet': {
                            'Name': 'api-{uid}.{root_domain}'.format(uid=integration.uid,
                                                                     root_domain=self._root_domain),
                            'Type': 'CNAME',
                            'TTL': 60,
                            'ResourceRecords': [
                                {
                                    'Value': self._proxy_domain
                                },
                            ],
                        }
                    }
                ]
            }
        )

    def destroy_integration_endpoint(self, integration_pk):
        integration = Integration.objects.first(pk=integration_pk).first()
        if not integration:
            return None, errors.MFAMissingInformationError('could not find integration `{0}`'.format(integration_pk))

        dns_change = self._cname_record_action('delete', integration)
        return dns_change

    def create_integration_endpoint(self, integration_pk):
        integration = Integration.objects.filter(pk=integration_pk).first()
        if not integration:
            return None, errors.MFAMissingInformationError('could not find integration `{0}`'.format(integration_pk))

        dns_change = self._cname_record_action('create', integration)
        return dns_change

