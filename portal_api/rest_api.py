#!/usr/bin/env python
# -- coding: utf-8 --

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PortalSerializer
from .utils import get_all_courses, get_active_courses
from openedx.core.lib.api.authentication import BearerAuthentication
from datetime import datetime as dt
from rest_framework import permissions
from rest_framework import status
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
import logging

logger = logging.getLogger(__name__)

class PortalApi(APIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        if not request.user.is_anonymous:
            serializer = PortalSerializer(data=request.data)
            if serializer.is_valid():
                result, courses = self.get_courses(serializer.data)
                if result == 'success':
                    return Response(data={'result':'success', 'courses': courses}, status=status.HTTP_200_OK)
                else:
                    return Response(data={'result':'error', 'error': courses}, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.error("PortalApi - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("PortalApi - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)

    def get_courses(self, data):
        """
            Get courses by filter type
        """
        platforms = settings.PORTAL_API_PLATFORMS or {}
        if platforms:
            if data['filter_type'] == 'all':
                courses = get_all_courses(platforms)
                return 'success', courses
            else:
                courses = get_active_courses(platforms)
                return 'success', courses
        else:
            return 'error', 'No hay plataformas configuradas'