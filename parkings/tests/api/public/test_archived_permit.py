from datetime import datetime, timedelta

import pytest
from django.urls import reverse

from parkings.factories.permit import create_permit
from parkings.models import ArchivedPermit, Permit

from ..utils import (
    check_list_endpoint_base_fields, check_method_status_codes, get)

list_url = reverse('public:v1:archivedpermit-list')

ITEM_KEYS = {'id', 'created_at', 'modified_at', 'domain', 'subjects', 'areas', 'archived_at'}


@pytest.fixture
def archived_permit():
    permit = create_permit(external_id='EXT-1', subject_count=2, area_count=1)
    permit.properties = {'secret': 'value'}
    permit.save()
    (archived, _count) = ArchivedPermit.archive_in_bulk(
        Permit.objects.filter(id=permit.id))
    return archived.get()


def test_disallowed_methods(api_client, archived_permit):
    check_method_status_codes(api_client, list_url, ('post', 'put', 'patch', 'delete'), 405)


def test_get_list_check_data(api_client, archived_permit):
    data = get(api_client, list_url)
    check_list_endpoint_base_fields(data)
    assert data['count'] == 1
    item = data['results'][0]
    assert set(item.keys()) == ITEM_KEYS
    assert len(item['subjects']) == 2
    assert all(set(x) == {'start_time', 'end_time'} for x in item['subjects'])
    assert all(set(x) == {'start_time', 'end_time', 'area'} for x in item['areas'])


def test_get_list_data_is_anonymized(api_client, archived_permit):
    content = str(get(api_client, list_url)).lower()
    assert 'registration_number' not in content
    assert 'address' not in content
    assert 'zip' not in content
    assert 'external_id' not in content
    assert 'secret' not in content


def test_filter_archived_at(api_client, archived_permit):
    fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
    later = datetime.strftime(archived_permit.archived_at + timedelta(hours=1), fmt)
    assert get(api_client, list_url + f'?archived_at__gte={later}')['count'] == 0
    assert get(api_client, list_url + f'?archived_at__lte={later}')['count'] == 1
