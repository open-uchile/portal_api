from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from rest_framework import serializers
import logging
logger = logging.getLogger(__name__)

class PortalSerializer(serializers.Serializer):
    filter_type = serializers.ChoiceField(
        choices=(
            ('all', 'all'),
            ('active', 'active')
        ),
        required=True
    )
