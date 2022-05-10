#!/usr/bin/env python
# -- coding: utf-8 --

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.urls import reverse
from urllib.parse import urlencode
from itertools import cycle
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from lms.djangoapps.courseware.courses import get_course_by_id, get_course_with_access
from xmodule.modulestore.django import modulestore
from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.course_action_state.models import CourseRerunState
from xmodule.modulestore import EdxJSONEncoder
from xmodule.course_module import DEFAULT_START_DATE, CourseFields
from openedx.core.djangoapps.models.course_details import CourseDetails
from lms.djangoapps.courseware.access import has_access
from .models import PortalApiCourse
from datetime import datetime as dt
from django.utils import timezone
import requests
import logging
import json
import six
import csv
import re
import io

logger = logging.getLogger(__name__)
URL_GET_COURSES = 'api/courses/v1/courses/'

def get_all_courses(platforms):
    """
        Get all courses on configured platforms
    """
    courses = {}
    for platform in platforms:
        aux_courses = get_course(platforms[platform])
        if aux_courses is None:
            courses[platform] = 'Error en obtener curso'
        else:
            courses[platform] = clean_data_course_all(aux_courses['results'], platforms[platform])
    external_courses = PortalApiCourse.objects.values()
    external_courses_list = list(external_courses)
    if len(external_courses_list) > 0:
        courses['external'] = external_courses_list
    return courses

def get_active_courses(platforms):
    """
        Get active courses on configured platforms
    """
    courses = {}
    for platform in platforms:
        aux_courses = get_course(platforms[platform])
        if aux_courses is None:
            courses[platform] = 'Error en obtener curso'
        else:
            courses[platform] = clean_data_course_active(aux_courses['results'], platforms[platform])
    external_courses = PortalApiCourse.objects.filter(end__gte=dt.now()).values()
    external_courses_list = list(external_courses)
    if len(external_courses_list) > 0:
        courses['external'] = external_courses_list
    return courses

def get_course(url):
    """
        Get courses
    """
    url_final = url+URL_GET_COURSES
    response = requests.get(url_final, timeout=10)
    if response.status_code != 200:
        logger.error('Error get courses, status_code: {}, response: {}'.format(response.status_code, response.text))
        return None
    return response.json()

def clean_data_course_all(courses, url_base):
    """
        Save only important data in all courses
    """
    data = []
    for course in courses:
        data.append({
            "course_id": course["course_id"],
            "start": course["start"],
            "end": course["end"],
            "image_url": course["media"]["image"]['raw'],
            "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
            "display_name": course["name"],
            "org": course["org"],
            "short_description": course["short_description"]
        })
    return data

def clean_data_course_active(courses, url_base):
    """
        Save only important data in active courses
    """
    data = []
    now = timezone.now()
    for course in courses:
        if course["end"] is not None:
            end = dt.strptime(course["end"], "%Y-%m-%dT%H:%M:%S%z")
            if end > now:
                data.append({
                    "course_id": course["course_id"],
                    "start": course["start"],
                    "end": course["end"],
                    "image_url": course["media"]["image"]['raw'],
                    "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                    "display_name": course["name"],
                    "org": course["org"],
                    "short_description": course["short_description"]
                })
    return data