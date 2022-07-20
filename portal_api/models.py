from django.contrib.auth.models import User
from django.db import models

from opaque_keys.edx.django.models import CourseKeyField

# Create your models here.

class PortalApiOrg(models.Model):
    org = models.CharField(max_length=50, unique=True, db_index=True)
    display_name = models.CharField(max_length=255, default='', blank=False)
    sort_number = models.PositiveSmallIntegerField(help_text = "Posición de la organización a mostrar en el portal", unique=True)
    url = models.CharField(max_length=255, default='', blank=True, help_text = "Agregar URL solo si quiere mostrar los cursos de la organización de manera automática.")
    
    def __str__(self):
        return '(%s) %s' % (self.sort_number, self.display_name)

class PortalApiCourse(models.Model):
    course_id = models.CharField(max_length=100, default='', blank=True)
    start = models.DateTimeField(null=True, default=None, blank=True)
    end = models.DateTimeField(null=True, default=None, blank=True)
    enrollment_start = models.DateTimeField(null=True, default=None, blank=True)
    enrollment_end = models.DateTimeField(null=True, default=None, blank=True)
    image_url = models.CharField(max_length=255, default='', blank=True)
    course_url = models.CharField(max_length=255, default='', blank=True)
    display_name = models.CharField(max_length=255, default='', blank=True)
    org = models.ForeignKey(PortalApiOrg, related_name="organization", on_delete=models.CASCADE, default=None)
    short_description = models.TextField('Short Description', blank=True, null=True)
    self_paced = models.BooleanField(default=False, help_text = "Enabled if is self-paced, Disabled if is instructor-paced")
    is_visible = models.BooleanField(default=True)
    
    def __str__(self):
        return '%s' % (self.course_id)