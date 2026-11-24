from django.db.models import Count, Q
from rest_framework import serializers, viewsets

from ...models import PermitArea
from ...pagination import Pagination
from ..common import WGS84InBBoxFilter
from ..utils import parse_timestamp_or_now
from .permissions import IsMonitor


class PermitAreaStatisticsSerializer(serializers.ModelSerializer):
    permit_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PermitArea
        fields = (
            'id',
            'permit_count',
        )


class PermitAreaStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Number of permits valid in each permit area at the given time.

    Only permits of the currently active permit series are counted.
    Areas without valid permits are included with a zero count.
    """
    permission_classes = [IsMonitor]
    queryset = PermitArea.objects.all()
    serializer_class = PermitAreaStatisticsSerializer
    pagination_class = Pagination
    bbox_filter_field = 'geom'
    filter_backends = [WGS84InBBoxFilter]
    bbox_filter_include_overlapping = True

    def get_queryset(self):
        time = parse_timestamp_or_now(self.request.query_params.get('time'))
        valid_items_q = (
            Q(permitlookupitem__permit__series__active=True) &
            Q(permitlookupitem__start_time__lte=time) &
            Q(permitlookupitem__end_time__gte=time))
        return (
            super().get_queryset()
            .filter(domain=self.request.user.monitor.domain)
            .annotate(permit_count=Count(
                'permitlookupitem__permit', filter=valid_items_q, distinct=True))
            .values('id', 'permit_count')
            .order_by('id'))
