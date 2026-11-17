import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, serializers, viewsets

from parkings.models import ArchivedPermit
from parkings.pagination import Pagination


class ArchivedPermitAnonymizedFilterSet(django_filters.FilterSet):

    class Meta:
        model = ArchivedPermit
        fields = {
            'created_at': ['lte', 'gte'],
            'archived_at': ['lte', 'gte'],
        }


class ArchivedPermitAnonymizedSerializer(serializers.ModelSerializer):
    subjects = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()

    class Meta:
        model = ArchivedPermit
        fields = [
            'id', 'created_at', 'modified_at', 'domain', 'subjects', 'areas',
            'archived_at',
        ]

    def get_subjects(self, obj):
        # Only validity times, no registration numbers or addresses
        return [
            {'start_time': x.get('start_time'), 'end_time': x.get('end_time')}
            for x in obj.subjects
        ]

    def get_areas(self, obj):
        return [
            {
                'start_time': x.get('start_time'),
                'end_time': x.get('end_time'),
                'area': x.get('area'),
            }
            for x in obj.areas
        ]


class PublicAPIArchivedPermitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = ArchivedPermit.objects.order_by('-archived_at', '-id')
    serializer_class = ArchivedPermitAnonymizedSerializer
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ArchivedPermitAnonymizedFilterSet
