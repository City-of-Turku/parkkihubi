import logging

import rest_framework_gis.pagination as gis_pagination
import rest_framework_gis.serializers as gis_serializers
from django.contrib.gis.gdal import GDALException
from rest_framework import serializers, viewsets

from ...models import PermitArea
from ..common import WGS84InBBoxFilter
from .permissions import IsMonitor

logger = logging.getLogger(__name__)

WGS84_SRID = 4326

# Square meters in square kilometer
M2_PER_KM2 = 1000000.0


def _looks_like_wgs84_degrees(geom):
    (min_x, min_y, max_x, max_y) = geom.extent
    return (
        geom.srid != WGS84_SRID
        and -180 <= min_x and max_x <= 180
        and -90 <= min_y and max_y <= 90)


class PermitAreaSerializer(gis_serializers.GeoFeatureModelSerializer):
    wgs84_geometry = gis_serializers.GeometrySerializerMethodField()
    area_km2 = serializers.SerializerMethodField()

    def get_wgs84_geometry(self, instance):
        geom = instance.geom
        if _looks_like_wgs84_degrees(geom):
            # Some old areas have lon/lat coordinates stored with the
            # GK25 SRID, which cannot be transformed.  Use them as is.
            logger.warning(
                "Permit area %s has WGS84 coordinates with SRID %s",
                instance.pk, geom.srid)
            result = geom.clone()
            result.srid = WGS84_SRID
            return result
        try:
            return geom.transform(WGS84_SRID, clone=True)
        except GDALException:
            logger.warning(
                "Cannot transform geometry of permit area %s", instance.pk)
            return None

    def get_area_km2(self, instance):
        return instance.geom.area / M2_PER_KM2

    class Meta:
        model = PermitArea
        geo_field = 'wgs84_geometry'
        fields = [
            'id',
            'identifier',
            'name',
            'area_km2',
        ]


class PermitAreaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsMonitor]
    queryset = PermitArea.objects.all().order_by('id')
    serializer_class = PermitAreaSerializer
    pagination_class = gis_pagination.GeoJsonPagination
    bbox_filter_field = 'geom'
    filter_backends = [WGS84InBBoxFilter]
    bbox_filter_include_overlapping = True

    def get_queryset(self):
        return super().get_queryset().filter(domain=self.request.user.monitor.domain)
