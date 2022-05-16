from django.contrib import admin
from .models import PortalApiCourse, PortalApiOrg

# Register your models here.


class PortalApiCourseAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'display_name', 'org', 'is_visible')
    search_fields = ['course_id', 'display_name', 'org', 'is_visible']

class PortalApiOrgAdmin(admin.ModelAdmin):
    list_display = ('org', 'display_name', 'sort_number',)
    search_fields = ['org', 'display_name', 'sort_number']

admin.site.register(PortalApiOrg, PortalApiOrgAdmin)
admin.site.register(PortalApiCourse, PortalApiCourseAdmin)
