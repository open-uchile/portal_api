#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock, MagicMock
from collections import namedtuple
from django.urls import reverse
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from urllib.parse import parse_qs
from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.tests.factories import CourseEnrollmentAllowedFactory, UserFactory, CourseEnrollmentFactory
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from django.test.utils import override_settings
from portal_api.serializers import PortalSerializer
from portal_api.rest_api import PortalApi
from portal_api.models import PortalApiCourse
from datetime import datetime as dt
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from unittest.case import SkipTest
import re
import json
import datetime
import urllib.parse


class TestPortalAPISerializers(ModuleStoreTestCase):
    def setUp(self):
        super(TestPortalAPISerializers, self).setUp()

    def test_portal_api_serializers(self):
        """
            test serializers
        """
        body = {
            "filter_type":'all'
        }
        serializer = PortalSerializer(data=body)
        self.assertTrue(serializer.is_valid())
    
    def test_portal_api_serializers_not_valid(self):
        """
            test wrong serializers
        """
        body = {
            "filter_type":'asd'
        }
        serializer = PortalSerializer(data=body)
        self.assertFalse(serializer.is_valid())
        body = {
            "asd":'asd'
        }
        serializer = PortalSerializer(data=body)
        self.assertFalse(serializer.is_valid())

class TestPortalAPI(ModuleStoreTestCase):
    def setUp(self):
        super(TestPortalAPI, self).setUp()
        self.course = CourseFactory.create(
            org='mss',
            course='999',
            display_name='2022',
            emit_signals=True)
        aux = CourseOverview.get_from_id(self.course.id)
        with patch('common.djangoapps.student.models.cc.User.save'):
            self.student = UserFactory(
                username='student',
                password='12345',
                email='student@edx.org')
            self.student_2 = UserFactory(
                username='student2',
                password='12345',
                email='student2@edx.org')

    @override_settings(PORTAL_API_PLATFORMS={'local':{'url':'https://test.test.ts/'}})
    @patch('requests.get')
    def test_portal_api_all_courses(self, get):
        """
            Test portal api
        """
        resp_data = {
            'results': [{
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': None, 
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+asdasd+2021', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2030-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+asdasd+2021'
            }],
            'pagination': {'next': 'https://test.test.ts/api/courses/v1/courses/?page=2', 'previous': None, 'count': 20, 'num_pages': 2}
        }
        get.side_effect = [namedtuple("Request",["status_code", "json"])(200, lambda:resp_data)]
        body = {
            "filter_type":'all'
        }
        expect = {
            'local': [{
                'end': None,
                'course_id': 'course-v1:eol+asdasd+2021', 
                'image_url': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
                'display_name': 'das', 
                'org': 'eol', 
                'short_description': None, 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
                'start': '2030-01-01T00:00:00Z'
            }]
        }
        result, courses = PortalApi().get_courses(body)
        self.assertEqual(result, 'success')
        self.assertEqual(courses, expect)
    
    @override_settings(PORTAL_API_PLATFORMS={'local':{'url':'https://test.test.ts/'}})
    @patch('requests.get')
    def test_portal_api_active_courses(self, get):
        """
            Test portal api
        """
        resp_data = {
            'results': [{
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2015-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+asdasd+2021', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2010-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+asdasd+2021'
            },
            {
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2099-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+test+2023', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2020-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+test+2023'
            }],
            'pagination': {'next': 'https://test.test.ts/api/courses/v1/courses/?page=2', 'previous': None, 'count': 20, 'num_pages': 2}
        }
        get.side_effect = [namedtuple("Request",["status_code", "json"])(200, lambda:resp_data)]
        body = {
            "filter_type":'active'
        }
        expect = {
            'local': [{
                'end': '2099-01-01T00:00:00Z',
                'course_id': 'course-v1:eol+test+2023', 
                'image_url': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg',
                'display_name': 'das', 
                'org': 'eol', 
                'short_description': None, 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+test+2023/about',
                'start': '2020-01-01T00:00:00Z', 
            }]
        }
        result, courses = PortalApi().get_courses(body)
        self.assertEqual(result, 'success')
        self.assertEqual(courses, expect)

    @override_settings(PORTAL_API_PLATFORMS={'local':{'url':'https://test.test.ts/'}})
    @patch('requests.get')
    def test_portal_api_error(self, get):
        """
            Test portal api
        """
        resp_data = 'Error'
        get.side_effect = [namedtuple("Request",["status_code", "text"])(403, resp_data)]
        body = {
            "filter_type":'all'
        }
        expect = {
            'local': []
        }
        result, courses = PortalApi().get_courses(body)
        self.assertEqual(result, 'success')
        self.assertEqual(courses, expect)

    @override_settings(PORTAL_API_PLATFORMS={'local':{'url':'https://test.test.ts/'}})
    @patch('requests.get')
    def test_portal_api_all_courses_with_model(self, get):
        """
            Test portal api with exteral courses
        """
        course_1 = PortalApiCourse.objects.create(
            course_id = 'course-v1:eol+test1+2022',
            start = dt.strptime('2000-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            end = dt.strptime('2001-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            image_url = 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
            course_url = 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
            display_name = 'Course test 1',
            org = 'eol',
            short_description = ''
        )
        course_2 = PortalApiCourse.objects.create(
            course_id = 'course-v1:eol+test2+2022',
            start = dt.strptime('2000-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            end = dt.strptime('2099-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            image_url = 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
            course_url = 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
            display_name = 'Course test 2',
            org = 'eol',
            short_description = ''
        )
        resp_data = {
            'results': [{
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': None, 
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+asdasd+2021', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2030-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+asdasd+2021'
            }],
            'pagination': {'next': 'https://test.test.ts/api/courses/v1/courses/?page=2', 'previous': None, 'count': 20, 'num_pages': 2}
        }
        get.side_effect = [namedtuple("Request",["status_code", "json"])(200, lambda:resp_data)]
        body = {
            "filter_type":'all'
        }
        expect = {
            'local': [{
                'end': None,
                'course_id': 'course-v1:eol+asdasd+2021', 
                'image_url': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
                'display_name': 'das', 
                'org': 'eol', 
                'short_description': None, 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
                'start': '2030-01-01T00:00:00Z'
            }],
            'external': [{
                'id': 1,
                'end': course_1.end,
                'course_id': 'course-v1:eol+test1+2022', 
                'image_url': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
                'display_name': 'Course test 1', 
                'org': 'eol', 
                'short_description': '', 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
                'start': course_1.start
            },
            {
                'id': 2,
                'end': course_2.end,
                'course_id': 'course-v1:eol+test2+2022', 
                'image_url': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
                'display_name': 'Course test 2', 
                'org': 'eol', 
                'short_description': '', 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
                'start': course_2.start
            }]
        }
        result, courses = PortalApi().get_courses(body)
        self.assertEqual(result, 'success')
        self.assertEqual(courses, expect)
    
    @override_settings(PORTAL_API_PLATFORMS={'local':{'url':'https://test.test.ts/'}})
    @patch('requests.get')
    def test_portal_api_active_courses_with_model(self, get):
        """
            Test portal api with exteral courses
        """
        course_1 = PortalApiCourse.objects.create(
            course_id = 'course-v1:eol+test1+2022',
            start = dt.strptime('2000-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            end = dt.strptime('2099-12-31T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            image_url = 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
            course_url = 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
            display_name = 'Course test 1',
            org = 'eol',
            short_description = ''
        )
        PortalApiCourse.objects.create(
            course_id = 'course-v1:eol+test2+2022',
            start = dt.strptime('2000-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            end = dt.strptime('2000-02-01T00:00:00Z', "%Y-%m-%dT%H:%M:%S%z"),
            image_url = 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
            course_url = 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
            display_name = 'Course test 2',
            org = 'eol',
            short_description = ''
        )
        resp_data = {
            'results': [{
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2015-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+asdasd+2021', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2010-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+asdasd+2021'
            },
            {
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2099-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+test+2023', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2020-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+test+2023'
            }],
            'pagination': {'next': 'https://test.test.ts/api/courses/v1/courses/?page=2', 'previous': None, 'count': 20, 'num_pages': 2}
        }
        get.side_effect = [namedtuple("Request",["status_code", "json"])(200, lambda:resp_data)]
        body = {
            "filter_type":'active'
        }
        expect = {
            'local': [{
                'end': '2099-01-01T00:00:00Z',
                'course_id': 'course-v1:eol+test+2023', 
                'image_url': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg',
                'display_name': 'das', 
                'org': 'eol', 
                'short_description': None, 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+test+2023/about',
                'start': '2020-01-01T00:00:00Z', 
            }],
            'external': [{
                'id': 1,
                'end': course_1.end,
                'course_id': 'course-v1:eol+test1+2022', 
                'image_url': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
                'display_name': 'Course test 1', 
                'org': 'eol', 
                'short_description': '', 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
                'start': course_1.start
            }]
        }
        result, courses = PortalApi().get_courses(body)
        self.assertEqual(result, 'success')
        self.assertEqual(courses, expect)

    @override_settings(PORTAL_API_PLATFORMS={'uabierta':{'url':'https://test.test.ts/'}})
    @patch('requests.get')
    def test_portal_api_all_courses_uabierta(self, get):
        """
            Test portal api
        """
        resp_data = {
            'results': [{
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': None, 
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+asdasd+2021', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2030-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+asdasd+2021'
            },
            {
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2099-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+test+2023', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'Certificación asda asdasd asd', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2020-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+test+2023'
            }],
            'pagination': {'next': 'https://test.test.ts/api/courses/v1/courses/?page=2', 'previous': None, 'count': 20, 'num_pages': 2}
        }
        get.side_effect = [namedtuple("Request",["status_code", "json"])(200, lambda:resp_data)]
        body = {
            "filter_type":'all'
        }
        expect = {
            'uabierta': [{
                'end': None,
                'course_id': 'course-v1:eol+asdasd+2021', 
                'image_url': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg',
                'display_name': 'das', 
                'org': 'eol', 
                'short_description': None, 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+asdasd+2021/about',
                'start': '2030-01-01T00:00:00Z'
            }]
        }
        result, courses = PortalApi().get_courses(body)
        self.assertEqual(result, 'success')
        self.assertEqual(courses, expect)
    
    @override_settings(PORTAL_API_PLATFORMS={'uabierta':{'url':'https://test.test.ts/'}})
    @patch('requests.get')
    def test_portal_api_active_courses_uabierta(self, get):
        """
            Test portal api
        """
        resp_data = {
            'results': [{
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2015-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+asdasd+2021', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+asdasd+2021+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2010-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+asdasd+2021'
            },
            {
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2099-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+test+2023', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'das', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2020-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+test+2023'
            },
            {
                'blocks_url': 'https://test.test.ts/api/courses/v2/blocks/?course_id=course-v1%3Aeol%2Basdasd%2B2021', 
                'effort': None, 
                'end': '2099-01-01T00:00:00Z',
                'enrollment_start': None, 
                'enrollment_end': None, 
                'id': 'course-v1:eol+test+2023', 
                'media': {
                    'course_image': {
                        'uri': '/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }, 
                    'course_video': {'uri': None}, 
                    'image': {
                        'raw': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'small': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg', 
                        'large': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg'
                        }
                    }, 
                'name': 'Certificación asdasvasd asdasd', 
                'number': 'asdasd', 
                'org': 'eol', 
                'short_description': None, 
                'start': '2020-01-01T00:00:00Z', 
                'start_display': None, 
                'start_type': 'empty', 
                'pacing': 'instructor', 
                'mobile_available': False, 
                'hidden': False, 
                'invitation_only': False, 
                'course_id': 'course-v1:eol+test+2023'
            }],
            'pagination': {'next': 'https://test.test.ts/api/courses/v1/courses/?page=2', 'previous': None, 'count': 20, 'num_pages': 2}
        }
        get.side_effect = [namedtuple("Request",["status_code", "json"])(200, lambda:resp_data)]
        body = {
            "filter_type":'active'
        }
        expect = {
            'uabierta': [{
                'end': '2099-01-01T00:00:00Z',
                'course_id': 'course-v1:eol+test+2023', 
                'image_url': 'https://test.test.ts/asset-v1:eol+test+2023+type@asset+block@images_course_image.jpg',
                'display_name': 'das', 
                'org': 'eol', 
                'short_description': None, 
                'course_url': 'https://test.test.ts/courses/course-v1:eol+test+2023/about',
                'start': '2020-01-01T00:00:00Z', 
            }]
        }
        result, courses = PortalApi().get_courses(body)
        self.assertEqual(result, 'success')
        self.assertEqual(courses, expect)
