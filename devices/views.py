from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from .models import DeviceKind
from .serializers import DeviceKindSerializer


class DeviceKindList(APIView):

    def get(self, request, format=None):
        return Response(
            DeviceKindSerializer(
                DeviceKind.objects.all(),
                many=True).data,
            status=status.HTTP_200_OK)
