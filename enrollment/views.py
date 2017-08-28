from __future__ import unicode_literals

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


from .models import Enrollment
from .serializers import EnrollmentSerializer, CreateEnrollmentSerializer, DevicePreparationSerializer

logger = logging.getLogger(__name__)


class EnrollmentDetail(APIView):
    def get(self, request, pk, format=None):
        enrollment = Enrollment.get_by_integration_and_pk(pk, request.auth)
        if not enrollment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            EnrollmentSerializer(enrollment).data, status=status.HTTP_200_OK)


class EnrollmentCompletion(APIView):
    def post(self, request, pk, format=None):
        enrollment = Enrollment.get_by_integration_and_pk(pk, request.auth)
        if not enrollment:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        err = enrollment.complete(request.data)
        if err:
            assert enrollment.status != Enrollment.STATUS_COMPLETE
            logger.error(
                'failed to complete enrollment `{0}`: {1}'.format(pk, err))
            return Response(err.message, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_201_CREATED, headers={
            'X-Client-Id': enrollment.client.pk,
        })


class EnrollmentDevicePreparation(APIView):
    def post(self, request, pk, format=None):
        serializer = DevicePreparationSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error('failed to parse device selection request: {0}'.
                         format(serializer.errors))
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        enrollment = Enrollment.get_by_integration_and_pk(pk, request.auth)
        if not enrollment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = serializer.validated_data

        err = enrollment.prepare(data)
        if err:
            logger.error(
                'failed to select device `{0}` for enrollment `{1}`: {2}'.
                format(data['kind'], pk, err))
            return Response(err.message, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            EnrollmentSerializer(enrollment).data, status=status.HTTP_200_OK)


class EnrollmentList(APIView):
    def post(self, request, format=None):
        serializer = CreateEnrollmentSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error('failed to validate create enrollment request: {0}'.
                        format(serializer.errors))
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        integration = request.auth

        enrollment, err = integration.enroll(data['username'])
        if err:
            logger.error('failed to create enrollment for user `{0}`: {1}'.
                         format(data['username'], err))
            return Response(err.message, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED)
