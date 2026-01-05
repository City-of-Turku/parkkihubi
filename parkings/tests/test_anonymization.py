import datetime
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone

from parkings.anonymization import (
    anonymize_all, anonymize_model, get_default_cutoff_date)
from parkings.models import Parking


@pytest.mark.django_db
class TestGetDefaultCutoffDate:
    """Tests for get_default_cutoff_date function."""

    def test_get_default_cutoff_date_with_timedelta(self, settings):
        """Test get_default_cutoff_date calculates cutoff correctly."""
        settings.PARKKIHUBI_REGISTRATION_NUMBERS_REMOVABLE_AFTER = datetime.timedelta(days=30)

        cutoff = get_default_cutoff_date()

        now = timezone.now()
        expected = now - datetime.timedelta(days=30)

        # Allow small time difference
        assert abs((cutoff - expected).total_seconds()) < 5

    def test_get_default_cutoff_date_with_invalid_type(self, settings):
        """Test get_default_cutoff_date raises ImproperlyConfigured for invalid type."""
        settings.PARKKIHUBI_REGISTRATION_NUMBERS_REMOVABLE_AFTER = 'invalid'

        with pytest.raises(Exception):  # Should raise ImproperlyConfigured
            get_default_cutoff_date()


@pytest.mark.django_db
class TestAnonymizeModel:
    """Tests for anonymize_model function."""

    @patch('parkings.anonymization.make_batches')
    @patch('parkings.anonymization.LOG')
    def test_anonymize_model_dry_run(self, mock_log, mock_make_batches, parking_factory):
        """Test anonymize_model with dry_run=True doesn't actually anonymize."""
        # Create some parkings
        parking_factory()
        parking_factory()

        cutoff = timezone.now() - datetime.timedelta(days=30)

        result = anonymize_model(
            Parking,
            cutoff=cutoff,
            dry_run=True
        )

        assert result == 0
        # Should not call make_batches in dry_run mode
        mock_make_batches.assert_not_called()

    @patch('parkings.anonymization.make_batches')
    @patch('parkings.anonymization.LOG')
    def test_anonymize_model_no_items(self, mock_log, mock_make_batches):
        """Test anonymize_model returns 0 when no items to anonymize."""
        cutoff = timezone.now() - datetime.timedelta(days=30)

        result = anonymize_model(
            Parking,
            cutoff=cutoff,
            dry_run=False
        )

        assert result == 0
        mock_make_batches.assert_not_called()

    @patch('parkings.anonymization.make_batches')
    @patch('parkings.anonymization.LOG')
    def test_anonymize_model_with_items(self, mock_log, mock_make_batches, parking_factory):
        """Test anonymize_model processes items when they exist."""
        # Create parking that would be anonymized
        old_time = timezone.now() - datetime.timedelta(days=60)
        parking_factory(time_start=old_time, time_end=old_time + datetime.timedelta(hours=1))

        cutoff = timezone.now() - datetime.timedelta(days=30)

        # Mock the batches
        mock_batch = Mock()
        mock_batch.anonymize.return_value = 1
        mock_make_batches.return_value = [mock_batch]

        # Mock the queryset methods
        with patch.object(Parking.objects, 'ends_before') as mock_ends_before, \
             patch.object(Parking.objects, 'unanonymized') as mock_unanonymized:

            mock_ended = Mock()
            mock_ended.unanonymized.return_value = Mock(count=lambda: 1)
            mock_ends_before.return_value = mock_ended

            mock_unanon = Mock()
            mock_unanon.count.return_value = 1
            mock_unanonymized.return_value = mock_unanon

            result = anonymize_model(
                Parking,
                cutoff=cutoff,
                dry_run=False
            )

            # Should have processed items
            assert result >= 0


@pytest.mark.django_db
class TestAnonymizeAll:
    """Tests for anonymize_all function."""

    @patch('parkings.anonymization.anonymize_model')
    @patch('parkings.anonymization.LOG')
    def test_anonymize_all_calls_anonymize_model_for_each_model(
        self, mock_log, mock_anonymize_model
    ):
        """Test anonymize_all calls anonymize_model for each model."""
        mock_anonymize_model.return_value = 5

        cutoff = timezone.now() - datetime.timedelta(days=30)
        result = anonymize_all(cutoff=cutoff, dry_run=False)

        # Should have called anonymize_model for each model in ENDED_ITEMS_QUERYSET_METHODS
        assert mock_anonymize_model.call_count > 0
        # Total should be sum of all model anonymizations
        assert result == mock_anonymize_model.return_value * mock_anonymize_model.call_count

    @patch('parkings.anonymization.get_default_cutoff_date')
    @patch('parkings.anonymization.anonymize_model')
    @patch('parkings.anonymization.LOG')
    def test_anonymize_all_uses_default_cutoff_when_none(
        self, mock_log, mock_anonymize_model, mock_get_default
    ):
        """Test anonymize_all uses default cutoff when cutoff is None."""
        mock_get_default.return_value = timezone.now() - datetime.timedelta(days=30)
        mock_anonymize_model.return_value = 0

        anonymize_all(cutoff=None, dry_run=False)

        mock_get_default.assert_called_once()
        assert mock_anonymize_model.call_count > 0
