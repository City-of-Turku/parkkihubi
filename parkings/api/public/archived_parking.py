
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, serializers, viewsets

from parkings.models import ArchivedParking
from parkings.pagination import Pagination


class ArchivedParkingAnonymizedFilterSet(django_filters.FilterSet):

    class Meta:
        model = ArchivedParking
        fields = {
            'time_start': ['lte', 'gte'],
            'archived_at': ['lte', 'gte'],
        }


class ArchivedParkingAnonymizedSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArchivedParking
        exclude = ['registration_number', 'normalized_reg_num']


class PublicAPIArchivedParkingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = ArchivedParking.objects.all().order_by('-time_start')
    serializer_class = ArchivedParkingAnonymizedSerializer
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ArchivedParkingAnonymizedFilterSet
