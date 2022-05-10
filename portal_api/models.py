from django.contrib.auth.models import User
from django.db import models

from opaque_keys.edx.django.models import CourseKeyField

# Create your models here.

class PortalApiCourse(models.Model):
    course_id = models.CharField(max_length=100, default='', blank=True)
    start = models.DateTimeField(null=True, default=None, blank=True)
    end = models.DateTimeField(null=True, default=None, blank=True)
    image_url = models.CharField(max_length=255, default='', blank=True)
    course_url = models.CharField(max_length=255, default='', blank=True)
    display_name = models.CharField(max_length=255, default='', blank=True)
    org = models.CharField(max_length=50, default='', blank=True)
    short_description = models.TextField('Short Description', blank=True, null=True)
