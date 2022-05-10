from django.contrib import admin
from .models import PortalApiCourse

# Register your models here.


class PortalApiCourseAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'display_name', 'org')
    search_fields = ['course_id', 'display_name', 'org']

admin.site.register(PortalApiCourse, PortalApiCourseAdmin)
