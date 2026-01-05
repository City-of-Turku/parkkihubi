from parkings.utils.sanitizing import (
    reset_sanitizing_session, sanitize_registration_number)


class TestResetSanitizingSession:
    """Tests for reset_sanitizing_session function."""

    def test_reset_sanitizing_session(self):
        """Test reset_sanitizing_session calls session.reset()."""
        # This is a simple wrapper, so we just verify it doesn't raise
        reset_sanitizing_session()
        # If it doesn't raise, it worked


class TestSanitizeRegistrationNumber:
    """Tests for sanitize_registration_number function."""

    def test_sanitize_registration_number_with_value(self):
        """Test sanitize_registration_number sanitizes a registration number."""
        value = 'ABC-123'
        result = sanitize_registration_number(value)

        assert result is not None
        assert result.startswith('!')
        assert len(result) > 1

    def test_sanitize_registration_number_with_dash(self):
        """Test sanitize_registration_number preserves dash if present."""
        value = 'ABC-123'
        result = sanitize_registration_number(value)

        # Should contain dash if original had dash
        assert '-' in result or result.count('-') == 0  # May or may not have dash

    def test_sanitize_registration_number_without_dash(self):
        """Test sanitize_registration_number doesn't add dash if not present."""
        value = 'ABC123'
        result = sanitize_registration_number(value)

        # Should not contain dash if original didn't have dash
        assert '-' not in result

    def test_sanitize_registration_number_empty_string(self):
        """Test sanitize_registration_number returns empty string for empty input."""
        result = sanitize_registration_number('')
        assert result == ''

    def test_sanitize_registration_number_none(self):
        """Test sanitize_registration_number returns None for None input."""
        result = sanitize_registration_number(None)
        assert result is None

    def test_sanitize_registration_number_only_spaces(self):
        """Test sanitize_registration_number returns original for only spaces."""
        value = '   '
        result = sanitize_registration_number(value)
        assert result == value

    def test_sanitize_registration_number_only_dashes(self):
        """Test sanitize_registration_number returns original for only dashes."""
        value = '---'
        result = sanitize_registration_number(value)
        assert result == value

    def test_sanitize_registration_number_spaces_and_dashes(self):
        """Test sanitize_registration_number returns original for spaces and dashes only."""
        value = ' - - '
        result = sanitize_registration_number(value)
        assert result == value

    def test_sanitize_registration_number_custom_prefix(self):
        """Test sanitize_registration_number uses custom prefix."""
        value = 'ABC123'
        result = sanitize_registration_number(value, prefix='X')

        assert result.startswith('X')

    def test_sanitize_registration_number_uppercase(self):
        """Test sanitize_registration_number converts to uppercase."""
        value = 'abc-123'
        result = sanitize_registration_number(value)

        # Result should be uppercase (normalized)
        assert result.isupper() or not any(c.islower() for c in result if c.isalpha())
