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
from collections import OrderedDict
from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.course_action_state.models import CourseRerunState
from xmodule.modulestore import EdxJSONEncoder
from xmodule.course_module import DEFAULT_START_DATE, CourseFields
from openedx.core.djangoapps.models.course_details import CourseDetails
from lms.djangoapps.courseware.access import has_access
from .models import PortalApiCourse, PortalApiOrg
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
URL_GET_COURSES = 'api/courses/v1/courses/?page_size=100'

def get_all_courses():
    """
        Get all courses on configured platforms
    """
    platforms = list(PortalApiOrg.objects.order_by("sort_number").values())
    courses = OrderedDict()
    for platform in platforms:
        courses[platform['org']] = course_model_to_list(PortalApiCourse.objects.filter(is_visible=True, org__id=platform['id']))
        if platform['url']:
            aux_courses = get_course(platform['url'])
            if aux_courses is not None:
                courses[platform['org']] += clean_data_course_all(aux_courses['results'], platform['url'], platform['org'])
    return courses

def get_active_courses():
    """
        Get active courses on configured platforms
    """
    platforms = list(PortalApiOrg.objects.order_by("sort_number").values())
    courses = OrderedDict()
    for platform in platforms:
        courses[platform['org']] = course_model_to_list(PortalApiCourse.objects.filter(is_visible=True, org__id=platform['id']))
        if platform['url']:
            aux_courses = get_course(platform['url'])
            if aux_courses is not None:
                courses[platform['org']] += clean_data_course_active(aux_courses['results'], platform['url'], platform['org'])
    return courses

def get_active_enroll_courses():
    """
        Get active courses on configured platforms with active enrollment
    """
    platforms = list(PortalApiOrg.objects.order_by("sort_number").values())
    courses = OrderedDict()
    for platform in platforms:
        courses[platform['org']] = course_model_to_list(PortalApiCourse.objects.filter(
            is_visible=True, 
            org__id=platform['id'], 
            enrollment_end__gte=timezone.now(), 
            enrollment_start__isnull=False,
            start__isnull=False,
            end__gte=timezone.now()))
        if platform['url']:
            aux_courses = get_course(platform['url'])
            if aux_courses is not None:
                courses[platform['org']] += clean_data_course_active_enroll(aux_courses['results'], platform['url'], platform['org'])
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

def course_model_to_list(courses):
    return [
        {
            "course_id": x.course_id,
            "start": x.start,
            "end": x.end,
            "image_url": x.image_url,
            "course_url": x.course_url,
            "display_name": x.display_name,
            "org": x.org.display_name,
            "short_description": x.short_description,
            "self_paced": x.self_paced,
            "enrollment_start": x.enrollment_start,
            "enrollment_end": x.enrollment_end
        } for x in courses
    ]

def clean_data_course_all(courses, url_base, platform):
    """
        Save only important data in all courses
    """
    data = []
    if platform == 'uabierta':
        for course in courses:
            if 'Certificación' not in course["name"]:
                data.append({
                    "course_id": course["course_id"],
                    "start": course["start"],
                    "start_display": course["start_display"] or None,
                    "end": course["end"],
                    "enrollment_start": course["enrollment_start"],
                    "enrollment_end": course["enrollment_end"],
                    "image_url": course["media"]["image"]['raw'],
                    "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                    "display_name": course["name"],
                    "org": course["org"],
                    "short_description": course["short_description"],
                    "self_paced": course["pacing"] == "self"
                })
    else:
        for course in courses:
            data.append({
                "course_id": course["course_id"],
                "start": course["start"],
                "end": course["end"],
                "enrollment_start": course["enrollment_start"],
                "enrollment_end": course["enrollment_end"],
                "image_url": course["media"]["image"]['raw'],
                "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                "display_name": course["name"],
                "org": course["org"],
                "short_description": course["short_description"],
                "self_paced": course["pacing"] == "self"
            })
    return data

def clean_data_course_active(courses, url_base, platform):
    """
        Save only important data in active courses
    """
    data = []
    now = timezone.now()
    if platform == 'uabierta':
        for course in courses:
            if 'Certificación' not in course["name"]:
                if course["end"] is not None:
                    end = dt.strptime(course["end"], "%Y-%m-%dT%H:%M:%S%z")
                    if end > now:
                        data.append({
                            "course_id": course["course_id"],
                            "start": course["start"],
                            "start_display": course["start_display"] or None,
                            "end": course["end"],
                            "image_url": course["media"]["image"]['raw'],
                            "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                            "display_name": course["name"],
                            "org": course["org"],
                            "enrollment_start": course["enrollment_start"],
                            "enrollment_end": course["enrollment_end"],
                            "short_description": course["short_description"],
                            "self_paced": course["pacing"] == "self"
                        })
                else:
                    data.append({
                            "course_id": course["course_id"],
                            "start": course["start"],
                            "start_display": course["start_display"] or None,
                            "end": course["end"],
                            "enrollment_start": course["enrollment_start"],
                            "enrollment_end": course["enrollment_end"],
                            "image_url": course["media"]["image"]['raw'],
                            "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                            "display_name": course["name"],
                            "org": course["org"],
                            "short_description": course["short_description"],
                            "self_paced": course["pacing"] == "self"
                        })
    else:
        for course in courses:
            if course["end"] is not None:
                end = dt.strptime(course["end"], "%Y-%m-%dT%H:%M:%S%z")
                if end > now:
                    data.append({
                        "course_id": course["course_id"],
                        "start": course["start"],
                        "end": course["end"],
                        "enrollment_start": course["enrollment_start"],
                        "enrollment_end": course["enrollment_end"],
                        "image_url": course["media"]["image"]['raw'],
                        "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                        "display_name": course["name"],
                        "org": course["org"],
                        "short_description": course["short_description"],
                        "self_paced": course["pacing"] == "self"
                    })
            else:
                data.append({
                        "course_id": course["course_id"],
                        "start": course["start"],
                        "end": course["end"],
                        "enrollment_start": course["enrollment_start"],
                        "enrollment_end": course["enrollment_end"],
                        "image_url": course["media"]["image"]['raw'],
                        "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                        "display_name": course["name"],
                        "org": course["org"],
                        "short_description": course["short_description"],
                        "self_paced": course["pacing"] == "self"
                    })
    return data

def clean_data_course_active_enroll(courses, url_base, platform):
    """
        Save only important data in active enrollment courses
    """
    data = []
    now = timezone.now()
    if platform == 'uabierta':
        for course in courses:
            if 'Certificación' not in course["name"]:
                if course["enrollment_end"] is not None and course["enrollment_start"] is not None:
                    enrollment_end = dt.strptime(course["enrollment_end"], "%Y-%m-%dT%H:%M:%S%z")
                    enrollment_start = dt.strptime(course["enrollment_start"], "%Y-%m-%dT%H:%M:%S%z")
                else:
                    enrollment_end = None
                    enrollment_start = None
                if course["end"] is not None:
                    end = dt.strptime(course["end"], "%Y-%m-%dT%H:%M:%S%z")
                    if end > now:
                        if enrollment_end and enrollment_start and enrollment_end > now:
                            data.append({
                                "course_id": course["course_id"],
                                "start": course["start"],
                                "start_display": course["start_display"] or None,
                                "end": course["end"],
                                "image_url": course["media"]["image"]['raw'],
                                "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                                "display_name": course["name"],
                                "org": course["org"],
                                "enrollment_start": course["enrollment_start"],
                                "enrollment_end": course["enrollment_end"],
                                "short_description": course["short_description"],
                                "self_paced": course["pacing"] == "self"
                            })
                else:
                    if enrollment_end and enrollment_start and enrollment_end > now:
                        data.append({
                                "course_id": course["course_id"],
                                "start": course["start"],
                                "start_display": course["start_display"] or None,
                                "end": course["end"],
                                "enrollment_start": course["enrollment_start"],
                                "enrollment_end": course["enrollment_end"],
                                "image_url": course["media"]["image"]['raw'],
                                "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                                "display_name": course["name"],
                                "org": course["org"],
                                "short_description": course["short_description"],
                                "self_paced": course["pacing"] == "self"
                            })
    else:
        for course in courses:
            if course["enrollment_end"] is not None and course["enrollment_start"] is not None:
                enrollment_end = dt.strptime(course["enrollment_end"], "%Y-%m-%dT%H:%M:%S%z")
                enrollment_start = dt.strptime(course["enrollment_start"], "%Y-%m-%dT%H:%M:%S%z")
            else:
                enrollment_end = None
                enrollment_start = None
            if course["end"] is not None:
                end = dt.strptime(course["end"], "%Y-%m-%dT%H:%M:%S%z")
                if end > now:
                    if enrollment_end and enrollment_start and enrollment_end > now:
                        data.append({
                            "course_id": course["course_id"],
                            "start": course["start"],
                            "end": course["end"],
                            "enrollment_start": course["enrollment_start"],
                            "enrollment_end": course["enrollment_end"],
                            "image_url": course["media"]["image"]['raw'],
                            "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                            "display_name": course["name"],
                            "org": course["org"],
                            "short_description": course["short_description"],
                            "self_paced": course["pacing"] == "self"
                        })
            else:
                if enrollment_end and enrollment_start and enrollment_end > now:
                    data.append({
                            "course_id": course["course_id"],
                            "start": course["start"],
                            "end": course["end"],
                            "enrollment_start": course["enrollment_start"],
                            "enrollment_end": course["enrollment_end"],
                            "image_url": course["media"]["image"]['raw'],
                            "course_url": "{}courses/{}/about".format(url_base,course["course_id"]),
                            "display_name": course["name"],
                            "org": course["org"],
                            "short_description": course["short_description"],
                            "self_paced": course["pacing"] == "self"
                        })
    return data


def get_platform_names():
    platforms = {}
    aux = PortalApiOrg.objects.values('org', 'display_name')
    for x in aux:
        platforms[x['org']] = x['display_name']
    return platforms