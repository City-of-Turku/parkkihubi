from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from parkings.factories.permit import create_permit_area, create_permit_series
from parkings.models import EnforcementDomain, Permit, PermitArea

list_url = reverse('monitoring:v1:permitarea-list')
stats_url = reverse('monitoring:v1:permitareastatistics-list')


def _make_area(domain, identifier):
    create_permit_area(identifier, domain)
    return PermitArea.objects.get(domain=domain, identifier=identifier)


def _make_permit(domain, series, area_identifier, reg_num='ABC-123',
                 start=timedelta(hours=-1), end=timedelta(hours=1)):
    now = timezone.now()
    return Permit.objects.create(
        domain=domain,
        series=series,
        subjects=[{
            'registration_number': reg_num,
            'start_time': str(now + start),
            'end_time': str(now + end),
            'address': None,
            'zip': None,
        }],
        areas=[{
            'start_time': str(now + start),
            'end_time': str(now + end),
            'area': area_identifier,
        }],
    )


def test_permit_areas_empty(monitoring_api_client):
    result = monitoring_api_client.get(list_url)
    assert result.status_code == status.HTTP_200_OK
    assert result.data['features'] == []


def test_permit_areas_only_from_own_domain(monitoring_api_client):
    domain = monitoring_api_client.monitor.domain
    other = EnforcementDomain.objects.create(code='OTHER', name='Other')
    area = _make_area(domain, 'A')
    _make_area(other, 'B')

    result = monitoring_api_client.get(list_url)
    assert result.status_code == status.HTTP_200_OK
    features = result.data['features']
    assert [f['id'] for f in features] == [area.id]
    assert features[0]['properties']['identifier'] == 'A'
    assert features[0]['geometry']['type'] == 'MultiPolygon'


def test_statistics_counts_valid_permits(monitoring_api_client, user):
    domain = monitoring_api_client.monitor.domain
    area_a = _make_area(domain, 'A')
    area_b = _make_area(domain, 'B')
    active = create_permit_series(active=True, owner=user)
    inactive = create_permit_series(active=False, owner=user)
    _make_permit(domain, active, 'A', 'AAA-111')
    _make_permit(domain, active, 'A', 'AAA-222')
    _make_permit(domain, active, 'B', 'BBB-111',
                 start=timedelta(hours=-3), end=timedelta(hours=-2))
    _make_permit(domain, inactive, 'B', 'BBB-222')

    result = monitoring_api_client.get(stats_url)
    assert result.status_code == status.HTTP_200_OK
    counts = {r['id']: r['permit_count'] for r in result.data['results']}
    assert counts == {area_a.id: 2, area_b.id: 0}


def test_statistics_with_specified_time(monitoring_api_client, user):
    domain = monitoring_api_client.monitor.domain
    area = _make_area(domain, 'A')
    series = create_permit_series(active=True, owner=user)
    _make_permit(domain, series, 'A')

    later = (timezone.now() + timedelta(hours=3)).isoformat()
    result = monitoring_api_client.get(stats_url, {'time': later})
    assert result.status_code == status.HTTP_200_OK
    assert result.data['results'] == [{'id': area.id, 'permit_count': 0}]


@pytest.mark.parametrize('url', [list_url, stats_url])
def test_requires_monitor(user_api_client, url):
    assert user_api_client.get(url).status_code == status.HTTP_403_FORBIDDEN


def test_permit_area_with_degrees_in_gk25_srid_is_used_as_wgs84(monitoring_api_client):
    domain = monitoring_api_client.monitor.domain
    area = _make_area(domain, 'A')
    # Degrees stored as if they were GK25 meters
    area.geom = MultiPolygon(
        Polygon(((22.2, 60.4), (22.3, 60.4), (22.3, 60.5), (22.2, 60.4))),
        srid=3879)
    area.save()

    result = monitoring_api_client.get(list_url)
    assert result.status_code == status.HTTP_200_OK
    coords = result.data['features'][0]['geometry']['coordinates']
    assert coords[0][0][0] == [22.2, 60.4]


def test_permit_area_with_untransformable_geometry_has_null_geometry(monitoring_api_client):
    domain = monitoring_api_client.monitor.domain
    _make_area(domain, 'A')

    with mock.patch(
            'django.contrib.gis.geos.GEOSGeometry.transform',
            side_effect=GDALException):
        result = monitoring_api_client.get(list_url)
    assert result.status_code == status.HTTP_200_OK
    assert result.data['features'][0]['geometry'] is None
