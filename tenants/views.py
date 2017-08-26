from __future__ import unicode_literals

import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Client, Integration, Tenant, TenantUser
from .serializers import IntegrationClientAuthDecisionSerializer, IntegrationClientAuthDecisionResponseSerializer, \
    CreateTenantSerializer, TenantSerializer, CreateIntegrationSerializer, IntegrationSerializer

logger = logging.getLogger(__name__)


class TenantIntegrationListView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        return Response(IntegrationSerializer(
            request.user.tenant_user.tenant.integrations.all(), many=True).data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = CreateIntegrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        assert isinstance(request.user, User)
        assert isinstance(request.user.tenant_user, TenantUser)
        assert isinstance(request.user.tenant_user.tenant, Tenant)

        data = serializer.data
        tenant = request.user.tenant_user.tenant
        logger.info('processing creation of new integration `{0}` for tenant `{1}`'.format(data['name'], tenant.name))

        res = IntegrationSerializer(Integration.create(
            tenant=tenant,
            name=data['name'],
            notes=data['notes']
        ))

        return Response(res.data, status=status.HTTP_201_CREATED)



class TenantsListView(APIView):
    def post(self, request, format=None):
        serializer = CreateTenantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.data
        logger.info('processing creation of new tenant `{0}`'.format(data['name']))

        # create the tenant entity
        res = TenantSerializer(Tenant.create(
            name=data['name'],
            email=data['administrator']['email'],
            first_name=data['administrator']['first_name'],
            last_name=data['administrator']['last_name'],
            password=data['administrator']['password']
        ))

        return Response(res.data, status=status.HTTP_201_CREATED)


class IntegrationClientAuthDecision(APIView):
    def post(self, request, format=None):
        serializer = IntegrationClientAuthDecisionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        assert request.auth is not None
        assert isinstance(request.auth, Integration)

        data = serializer.validated_data

        logger.info('processing auth decision for username `{0}`'.format(data['username']))

        # attempt to obtain a client with the given username
        client = Client.objects.filter(
            username=data['username'],
            integration=request.auth
        ).first()

        # if we don't have a client, send an enrollment signal
        if not client:
            logger.info('auth informs that username `{0}` is not present; must enroll'.format(data['username']))

            res = IntegrationClientAuthDecisionResponseSerializer({
                'result': IntegrationClientAuthDecisionResponseSerializer.RESULT_ENROLL
            })

            return Response(res.data, status=status.HTTP_200_OK)

        # if we have a client in a status different than active, handle it here
        if client.status != Client.STATUS_ACTIVE:
            logger.info(
                'auth informs that username `{0}` is not to undergo 2fa; status is `{1}`'.format(data['username'],
                                                                                                 client.get_status_display()))
            res = IntegrationClientAuthDecisionResponseSerializer({
                'result': IntegrationClientAuthDecisionResponseSerializer.RESULT_ALLOW if client.status == Client.STATUS_BYPASS else IntegrationClientAuthDecisionResponseSerializer.RESULT_DENY
            })

            return Response(res.data, status=status.HTTP_200_OK)

        # we have a client, and it is neither exempt or or denied, so must go through 2nd factor
        res = IntegrationClientAuthDecisionResponseSerializer({
            'result': IntegrationClientAuthDecisionResponseSerializer.RESULT_CHALLENGE,
            'devices': client.devices.all()
        })

        return Response(res.data, status=status.HTTP_200_OK)
