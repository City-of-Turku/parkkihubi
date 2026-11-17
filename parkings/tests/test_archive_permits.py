import pytest
from django.core.management import call_command

from parkings.factories.permit import create_permit
from parkings.models import ArchivedPermit, Permit

pytestmark = pytest.mark.django_db


def test_archive_permits_moves_ended_permits_and_anonymizes():
    permit = create_permit(subject_count=2, area_count=1)
    permit_id = permit.id
    areas = permit.areas
    # Make the permit end long ago
    permit.subjects = [
        {**x, "start_time": "2020-01-01T00:00:00Z",
         "end_time": "2020-01-02T00:00:00Z"} for x in permit.subjects]
    permit.areas = [
        {**x, "start_time": "2020-01-01T00:00:00Z",
         "end_time": "2020-01-02T00:00:00Z"} for x in areas]
    permit.save()

    call_command("archive_permits", "--keep-days", "30", verbosity=0)

    assert not Permit.objects.filter(id=permit_id).exists()
    archived = ArchivedPermit.objects.get(id=permit_id)
    assert archived.archived_at
    assert [x["registration_number"] for x in archived.subjects] == ["", ""]
    assert archived.areas == permit.areas


def test_archive_permits_keeps_ongoing_permits():
    permit = create_permit()

    call_command("archive_permits", "--keep-days", "30", verbosity=0)

    assert Permit.objects.filter(id=permit.id).exists()
    assert not ArchivedPermit.objects.exists()
