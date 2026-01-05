import csv
import io
from unittest.mock import Mock

import pytest
from django.contrib import admin
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import RequestFactory

from parkings.admin_utils import ReadOnlyAdmin, WithAreaField, export_as_csv
from parkings.models import EnforcementDomain


@pytest.mark.django_db
class TestReadOnlyAdmin:
    """Tests for ReadOnlyAdmin class."""

    def test_get_readonly_fields(self):
        """Test get_readonly_fields returns all field names."""
        admin_instance = ReadOnlyAdmin(EnforcementDomain, admin.site)
        obj = EnforcementDomain.objects.create(code='TEST', name='Test Domain')

        readonly_fields = admin_instance.get_readonly_fields(None, obj)

        # Should return all field names
        assert 'id' in readonly_fields
        assert 'code' in readonly_fields
        assert 'name' in readonly_fields
        assert 'created_at' in readonly_fields
        assert 'modified_at' in readonly_fields

    def test_has_add_permission(self):
        """Test has_add_permission always returns False."""
        admin_instance = ReadOnlyAdmin(EnforcementDomain, admin.site)

        assert admin_instance.has_add_permission(None) is False

    def test_has_change_permission(self):
        """Test has_change_permission always returns False."""
        admin_instance = ReadOnlyAdmin(EnforcementDomain, admin.site)

        assert admin_instance.has_change_permission(None) is False
        assert admin_instance.has_change_permission(None, None) is False

    def test_has_delete_permission(self):
        """Test has_delete_permission always returns False."""
        admin_instance = ReadOnlyAdmin(EnforcementDomain, admin.site)

        assert admin_instance.has_delete_permission(None) is False
        assert admin_instance.has_delete_permission(None, None) is False


@pytest.mark.django_db
class TestWithAreaField:
    """Tests for WithAreaField mixin."""

    def test_area_with_geom_km2(self):
        """Test area method returns area in km² when area_scale is 1000000."""
        admin_instance = WithAreaField()
        admin_instance.area_scale = 1000000

        # Create a MultiPolygon with known area (approximately 1 km²)
        polygon = Polygon(((0, 0), (0, 1000), (1000, 1000), (1000, 0), (0, 0)), srid=3067)
        geom = MultiPolygon(polygon, srid=3067)
        obj = EnforcementDomain.objects.create(
            code='TEST',
            name='Test',
            geom=geom
        )

        result = admin_instance.area(obj)

        # Should be approximately 1.0 km² (1000m * 1000m = 1,000,000 m² = 1 km²)
        assert 'km²' in result
        assert float(result.split()[0]) > 0.9  # Allow some tolerance

    def test_area_with_geom_m2(self):
        """Test area method returns area in m² when area_scale is 1."""
        admin_instance = WithAreaField()
        admin_instance.area_scale = 1

        polygon = Polygon(((0, 0), (0, 100), (100, 100), (100, 0), (0, 0)), srid=3067)
        geom = MultiPolygon(polygon, srid=3067)
        obj = EnforcementDomain.objects.create(
            code='TEST',
            name='Test',
            geom=geom
        )

        result = admin_instance.area(obj)

        # Should be in m²
        assert 'm²' in result
        assert float(result.split()[0]) > 0  # Should have some area

    def test_area_without_geom(self):
        """Test area method returns empty string when geom is None."""
        admin_instance = WithAreaField()
        obj = EnforcementDomain.objects.create(code='TEST', name='Test', geom=None)

        result = admin_instance.area(obj)

        assert result == ''


@pytest.mark.django_db
class TestExportAsCsv:
    """Tests for export_as_csv function."""

    def test_export_as_csv_basic(self):
        """Test export_as_csv exports all fields."""
        # Create test objects
        EnforcementDomain.objects.create(code='TEST1', name='Test Domain 1')
        EnforcementDomain.objects.create(code='TEST2', name='Test Domain 2')

        # Create mock admin
        mock_admin = Mock()
        mock_admin.model = EnforcementDomain
        mock_admin.model._meta.model_name = 'enforcementdomain'
        mock_admin.exclude_csv_fields = []

        # Create request
        factory = RequestFactory()
        request = factory.get('/')

        # Get queryset
        queryset = EnforcementDomain.objects.all()

        # Call function
        response = export_as_csv(mock_admin, request, queryset)

        # Check response
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']
        assert 'enforcementdomain.csv' in response['Content-Disposition']

        # Parse CSV
        content = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # Check header row
        assert len(rows) > 0
        header = rows[0]
        assert 'id' in header
        assert 'code' in header
        assert 'name' in header

        # Check data rows (should have 2 objects)
        assert len(rows) == 3  # 1 header + 2 data rows

    def test_export_as_csv_with_excluded_fields(self):
        """Test export_as_csv excludes specified fields."""
        domain = EnforcementDomain.objects.create(code='TEST', name='Test Domain')

        # Create mock admin with excluded fields
        mock_admin = Mock()
        mock_admin.model = EnforcementDomain
        mock_admin.model._meta.model_name = 'enforcementdomain'
        mock_admin.exclude_csv_fields = ['created_at', 'modified_at']

        # Create request
        factory = RequestFactory()
        request = factory.get('/')

        # Get queryset
        queryset = EnforcementDomain.objects.filter(id=domain.id)

        # Call function
        response = export_as_csv(mock_admin, request, queryset)

        # Parse CSV
        content = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # Check header row doesn't contain excluded fields
        header = rows[0]
        assert 'created_at' not in header
        assert 'modified_at' not in header
        # But should contain other fields
        assert 'code' in header
        assert 'name' in header

    def test_export_as_csv_empty_queryset(self):
        """Test export_as_csv handles empty queryset."""
        # Create mock admin
        mock_admin = Mock()
        mock_admin.model = EnforcementDomain
        mock_admin.model._meta.model_name = 'enforcementdomain'
        mock_admin.exclude_csv_fields = []

        # Create request
        factory = RequestFactory()
        request = factory.get('/')

        # Empty queryset
        queryset = EnforcementDomain.objects.none()

        # Call function
        response = export_as_csv(mock_admin, request, queryset)

        # Parse CSV
        content = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # Should only have header row
        assert len(rows) == 1
        assert len(rows[0]) > 0  # Header should have fields
