from __future__ import unicode_literals

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Challenge
from .serializers import CreateChallengeSerializer, ChallengeSerializer

logger = logging.getLogger(__name__)


class ChallengeList(APIView):
    def post(self, request, format=None):
        serializer = CreateChallengeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # get the integration
        integration = request.auth

        # get the client associated with this username
        data = serializer.validated_data
        client = integration.clients.filter(username=data['username']).first()

        if not client:
            logger.error(
                'attempt to challenge invalid username `{0}`'.format(data['username']))
            return Response(status=status.HTTP_404_NOT_FOUND)

        # create a challenge, and return the results
        challenge, err = request.auth.challenge(client, data)
        if err:
            logger.error('failed to create challenge for username `{0}`: {1}'.format(
                client.username, err))
            return Response(err, status=status.HTTP_400_BAD_REQUEST)
        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED)


class ChallengeDetailView(APIView):
    def get(self, request, pk, format=None):
        challenge = Challenge.get_by_integration_and_pk(pk, request.auth)

        if not challenge:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_200_OK)


class ChallengeCompletionView(APIView):
    def post(self, request, pk, format=None):
        challenge = Challenge.get_by_integration_and_pk(pk, request.auth)
        if not challenge:
            return Response(status=status.HTTP_404_NOT_FOUND)

        _, err = challenge.complete(request.data)

        if err:
            logger.error(
                'failed to complete challenge `{0}`: {1}'.format(pk, err.message))
            return Response(err.message, status=status.HTTP_400_BAD_REQUEST)

        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_200_OK)
