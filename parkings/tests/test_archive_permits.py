from unittest import mock

import pytest
from django.core.management import call_command

from parkings.factories.permit import create_permit
from parkings.management.commands import archive_permits
from parkings.models import ArchivedPermit, Permit
from parkings.tests.utils import call_mgmt_cmd_with_output

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


def _create_ended_permits(count):
    permits = []
    for _ in range(count):
        permit = create_permit(subject_count=1, area_count=1)
        permit.subjects = [
            {**x, "start_time": "2020-01-01T00:00:00Z",
             "end_time": "2020-01-02T00:00:00Z"} for x in permit.subjects]
        permit.areas = [
            {**x, "start_time": "2020-01-01T00:00:00Z",
             "end_time": "2020-01-02T00:00:00Z"} for x in permit.areas]
        permit.save()
        permits.append(permit)
    return permits


def test_archive_permits_nothing_to_archive():
    create_permit()
    (_, out, _) = call_mgmt_cmd_with_output(
        archive_permits.Command, "--keep-days", "30")
    assert "Nothing to archive" in out


def test_archive_permits_dry_run_keeps_permits():
    _create_ended_permits(2)
    (_, out, _) = call_mgmt_cmd_with_output(
        archive_permits.Command, "--keep-days", "30", "--dry-run")
    assert "Would archive 2" in out
    assert "Would have archived 2 permits" in out
    assert Permit.objects.count() == 2
    assert not ArchivedPermit.objects.exists()


def test_archive_permits_limit_and_batches():
    _create_ended_permits(3)
    (_, out, _) = call_mgmt_cmd_with_output(
        archive_permits.Command, "--keep-days", "30",
        "--limit", "2", "--batch-size", "1")
    assert "Will archive 2 (out of 3) permits" in out
    assert ArchivedPermit.objects.count() == 2
    assert Permit.objects.count() == 1


def test_archive_permits_interrupted():
    _create_ended_permits(1)
    with mock.patch(
            "parkings.models.permit.PermitQuerySet.archive",
            side_effect=KeyboardInterrupt):
        (_, out, _) = call_mgmt_cmd_with_output(
            archive_permits.Command, "--keep-days", "30")
    assert "Interrupted" in out
    assert Permit.objects.count() == 1


def test_archived_permit_helpers():
    [permit] = _create_ended_permits(1)
    (archived_qs, count) = ArchivedPermit.archive_in_bulk(
        Permit.objects.filter(id=permit.id))
    assert count == 1
    archived = archived_qs.get()
    assert "(archived)" in str(archived)
    assert archived.archive() is archived
    # Archiving already archived permits is a no-op
    (qs, count) = ArchivedPermit.archive_in_bulk(ArchivedPermit.objects.all())
    assert count == 0
    assert not qs.exists()


def test_permit_queryset_archive_callbacks():
    _create_ended_permits(2)
    pre = []
    post = []
    total = Permit.objects.all().archive(
        batch_size=1,
        pre_archive_callback=lambda batch, n: pre.append(n),
        post_archive_callback=lambda batch, n: post.append(n))
    assert total == 2
    assert pre == [0, 1]
    assert post == [1, 2]


def test_permit_anonymize_and_unanonymized():
    permits = _create_ended_permits(2)
    assert Permit.objects.unanonymized().count() == 2
    count = Permit.objects.filter(id=permits[0].id).anonymize()
    assert count == 1
    assert Permit.objects.unanonymized().count() == 1
    permit = Permit.objects.get(id=permits[0].id)
    assert all(x["registration_number"] == "" for x in permit.subjects)
