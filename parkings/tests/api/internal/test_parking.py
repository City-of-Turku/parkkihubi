import json
from datetime import datetime

import pytest
import pytz
from django.core.urlresolvers import reverse
from django.utils.timezone import utc

from parkings.models import Parking

from ..utils import (
    ALL_METHODS, check_list_endpoint_base_fields, check_method_status_codes, check_response_objects, get,
    get_ids_from_results
)

list_url = reverse('internal:v1:parking-list')


def get_detail_url(obj):
    return reverse('internal:v1:parking-detail', kwargs={'pk': obj.pk})


def check_parking_data_keys(parking_data):
    assert set(parking_data.keys()) == {
        'id', 'created_at', 'modified_at', 'parking_area',
        'location', 'operator', 'registration_number',
        'terminal', 'terminal_number',
        'time_start', 'time_end', 'zone', 'status',
    }


def check_parking_data_matches_parking_object(parking_data, parking_obj):
    """
    Check that a parking data dict and an actual Parking object match.
    """

    # string and integer valued fields should match 1:1
    for field in {'registration_number', 'zone'}:
        assert parking_data[field] == getattr(parking_obj, field)

    assert parking_data['id'] == str(parking_obj.id)
    assert parking_data['created_at'] == parking_obj.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    assert parking_data['modified_at'] == parking_obj.modified_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    assert parking_data['time_start'] == parking_obj.time_start.strftime('%Y-%m-%dT%H:%M:%SZ')
    assert parking_data['time_end'] == parking_obj.time_end.strftime('%Y-%m-%dT%H:%M:%SZ')
    assert parking_data['operator'] == str(parking_obj.operator_id)
    assert parking_data['location'] == json.loads(parking_obj.location.geojson)


def test_other_than_staff_cannot_do_anything(api_client, operator_api_client, parking):
    urls = (list_url, get_detail_url(parking))
    check_method_status_codes(api_client, urls, ALL_METHODS, 401)
    check_method_status_codes(operator_api_client, urls, ALL_METHODS, 403, error_code='permission_denied')


def test_disallowed_methods(staff_api_client, parking):
    disallowed_methods = ('post', 'put', 'patch', 'delete')
    urls = (list_url, get_detail_url(parking))
    check_method_status_codes(staff_api_client, urls, disallowed_methods, 405)


def test_get_list_check_data(staff_api_client, parking):
    data = get(staff_api_client, list_url)
    assert len(data['results']) == 1
    parking_data = data['results'][0]
    check_parking_data_keys(parking_data)
    check_parking_data_matches_parking_object(data['results'][0], parking)


def test_get_detail_check_data(staff_api_client, parking):
    parking_data = get(staff_api_client, get_detail_url(parking))
    check_parking_data_keys(parking_data)
    check_parking_data_matches_parking_object(parking_data, parking)


def test_list_endpoint_base_fields(staff_api_client):
    parking_data = get(staff_api_client, list_url)
    check_list_endpoint_base_fields(parking_data)


def test_is_valid_field(staff_api_client, past_parking, current_parking, future_parking,
                        current_parking_without_end_time, future_parking_without_end_time):
    parking_data = get(staff_api_client, get_detail_url(past_parking))
    assert parking_data['status'] == Parking.NOT_VALID

    parking_data = get(staff_api_client, get_detail_url(current_parking))
    assert parking_data['status'] == Parking.VALID

    parking_data = get(staff_api_client, get_detail_url(future_parking))
    assert parking_data['status'] == Parking.NOT_VALID

    parking_data = get(staff_api_client, get_detail_url(current_parking_without_end_time))
    assert parking_data['status'] == Parking.VALID

    parking_data = get(staff_api_client, get_detail_url(future_parking_without_end_time))
    assert parking_data['status'] == Parking.NOT_VALID


def test_is_valid_filter(staff_api_client, past_parking, current_parking, future_parking,
                         current_parking_without_end_time, future_parking_without_end_time):
    response = get(staff_api_client, list_url + '?status=valid')
    check_response_objects(response, {current_parking, current_parking_without_end_time})

    response = get(staff_api_client, list_url + '?status=not_valid')
    check_response_objects(response, {past_parking, future_parking, future_parking_without_end_time})


def test_registration_number_filter(operator, staff_api_client, parking_factory):
    parking_1 = parking_factory(registration_number='ABC-123', operator=operator)
    parking_2 = parking_factory(registration_number='ZYX-987', operator=operator)
    parking_3 = parking_factory(registration_number='ZYX-987', operator=operator)

    results = get(staff_api_client, list_url + '?registration_number=ABC-123')['results']
    assert get_ids_from_results(results) == {parking_1.id}

    results = get(staff_api_client, list_url + '?registration_number=ZYX-987')['results']
    assert get_ids_from_results(results) == {parking_2.id, parking_3.id}

    results = get(staff_api_client, list_url + '?registration_number=LOL-777')['results']
    assert len(results) == 0


@pytest.mark.parametrize('filtering, expected_parking_indexes', [
    ('', [0, 1]),
    ('time_start__lte=2014-01-01T12:00:00Z', [0, 1]),
    ('time_start__lte=2014-01-01T11:59:59Z', [0]),
    ('time_end__gte=2014-01-01T12:00:00Z', [0, 1]),
    ('time_end__gte=2014-01-01T12:00:01Z', [1]),
    ('time_start__gte=2012-01-01T12:00:00Z', [0, 1]),
    ('time_start__gte=2012-01-01T12:00:01Z', [1]),
    ('time_end__lte=2016-01-01T12:00:00Z', [0, 1]),
    ('time_end__lte=2016-01-01T11:59:59Z', [0]),
    ('time_start__gte=2011-01-01T12:00:00Z&time_end__lte=2015-01-01T12:00:00Z', [0]),
    ('time_start__gte=2013-01-01T12:00:00Z&time_end__lte=2015-01-01T12:00:00Z', []),
])
def test_time_filters(operator, staff_api_client, parking_factory, filtering, expected_parking_indexes):
    parkings = [
        parking_factory(
            time_start=datetime(2012, 1, 1, 12, 0, 0, tzinfo=utc),
            time_end=datetime(2014, 1, 1, 12, 0, 0, tzinfo=utc),
            operator=operator
        ),
        parking_factory(
            time_start=datetime(2014, 1, 1, 12, 0, 0, tzinfo=utc),
            time_end=datetime(2016, 1, 1, 12, 0, 0, tzinfo=utc),
            operator=operator
        )
    ]
    expected_parkings = set(parkings[index] for index in expected_parking_indexes)

    response = get(staff_api_client, list_url + '?' + filtering)
    check_response_objects(response, expected_parkings)


@pytest.mark.parametrize('filtering, expected_visibility', [
    ('time_end__lte=2020-01-01T12:00:00Z', False),
    ('time_end__gte=2020-01-01T12:00:00Z', True),
])
def test_end_time_filters_no_end_time(operator, staff_api_client, parking_factory, filtering, expected_visibility):
    parking = parking_factory(
        time_start=datetime(2018, 1, 1, tzinfo=pytz.utc),
        time_end=None,
        operator=operator)

    response = get(staff_api_client, list_url + '?' + filtering)
    check_response_objects(response, parking if expected_visibility else [])
