import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework import status

from parkings.api.auth import views

User = get_user_model()


@pytest.fixture
def client():
    """Django test client for session-based authentication."""
    return Client()


@pytest.mark.django_db
class TestCheckAuth:
    """Tests for check_auth view."""

    def test_check_auth_authenticated_staff(self, client, user_factory):
        """Test check_auth returns 200 with user info when authenticated as staff."""
        # Default REST_FRAMEWORK permission is IsAdminUser, which requires is_staff=True
        user = user_factory(is_staff=True)
        client.force_login(user)

        url = reverse('auth:v1:check')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['authenticated'] is True
        assert data['username'] == user.username

    def test_check_auth_authenticated_non_staff(self, client, user_factory):
        """Test check_auth returns 403 for authenticated non-staff users."""
        # Default REST_FRAMEWORK permission is IsAdminUser
        user = user_factory(is_staff=False)
        client.force_login(user)

        url = reverse('auth:v1:check')
        response = client.get(url)

        # Should return 403 due to IsAdminUser permission
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_check_auth_unauthenticated(self, client):
        """Test check_auth returns 401 or 403 when not authenticated."""
        url = reverse('auth:v1:check')
        response = client.get(url)

        # Should return 401 (unauthorized) or 403 (forbidden due to IsAdminUser)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

        # The view logic checks authentication, but permission class might return 403 first
        # Both are valid test coverage scenarios


@pytest.mark.django_db
class TestDashboardLogin:
    """Tests for dashboard_login view."""

    def test_dashboard_login_with_next_url(self, client):
        """Test dashboard_login stores next URL in session and redirects."""
        next_url = '/dashboard/some-page'
        url = reverse('dashboard_login') + f'?next={next_url}'

        response = client.get(url, follow=False)

        assert response.status_code == 302
        assert response.url == f'/admin/login/?next={next_url}'
        # Check session was modified
        assert client.session.get('dashboard_next') == next_url

    def test_dashboard_login_without_next_url_unauthenticated(self, client):
        """Test dashboard_login sets dashboard_login flag when no next URL."""
        url = reverse('dashboard_login')

        response = client.get(url, follow=False)

        assert response.status_code == 302
        assert response.url == '/admin/login/'
        # Check session flag was set
        assert client.session.get('dashboard_login') is True

    def test_dashboard_login_without_next_url_authenticated(self, client, user_factory):
        """Test dashboard_login redirects authenticated user directly."""
        user = user_factory()
        client.force_login(user)

        url = reverse('dashboard_login')

        response = client.get(url, follow=False)

        # When authenticated, dashboard_login calls login_redirect which redirects to dashboard
        # The redirect might go directly to /dashboard/ or via /login-redirect/
        assert response.status_code == 302
        assert response.url in ['/login-redirect/', '/dashboard/']


@pytest.mark.django_db
class TestLoginRedirect:
    """Tests for login_redirect view."""

    def test_login_redirect_from_query_string(self, client, user_factory):
        """Test login_redirect uses next from query string."""
        user = user_factory()
        client.force_login(user)

        next_url = '/dashboard/custom-page'
        url = reverse('login_redirect') + f'?next={next_url}'

        response = client.get(url, follow=False)

        assert response.status_code == 302
        assert response.url == next_url

    def test_login_redirect_from_session_dashboard_next(self, client, user_factory):
        """Test login_redirect uses next from session dashboard_next."""
        user = user_factory()
        client.force_login(user)

        # Set session value
        session = client.session
        session['dashboard_next'] = '/dashboard/session-page'
        session.save()

        url = reverse('login_redirect')
        response = client.get(url, follow=False)

        assert response.status_code == 302
        assert response.url == '/dashboard/session-page'
        # Check session was cleared
        assert 'dashboard_next' not in client.session

    def test_login_redirect_from_session_dashboard_flag(self, client, user_factory):
        """Test login_redirect uses dashboard flag from session."""
        user = user_factory()
        client.force_login(user)

        # Set session flag
        session = client.session
        session['dashboard_login'] = True
        session.save()

        url = reverse('login_redirect')
        response = client.get(url, follow=False)

        assert response.status_code == 302
        assert response.url == '/dashboard/'
        # Check session flag was cleared
        assert 'dashboard_login' not in client.session

    def test_login_redirect_from_social_django_next(self, client, user_factory):
        """Test login_redirect uses next from social_django session."""
        user = user_factory()
        client.force_login(user)

        # Set social_django session value
        session = client.session
        session['next'] = '/dashboard/social-page'
        session.save()

        url = reverse('login_redirect')
        response = client.get(url, follow=False)

        assert response.status_code == 302
        assert response.url == '/dashboard/social-page'
        # Check session was cleared
        assert 'next' not in client.session

    def test_login_redirect_from_social_django_social_auth_next(self, client, user_factory):
        """Test login_redirect uses next from social_auth_next session."""
        user = user_factory()
        client.force_login(user)

        # Set social_auth_next session value
        session = client.session
        session['social_auth_next'] = '/dashboard/social-auth-page'
        session.save()

        url = reverse('login_redirect')
        response = client.get(url, follow=False)

        assert response.status_code == 302
        assert response.url == '/dashboard/social-auth-page'

    def test_login_redirect_from_referer_dashboard(self, client, user_factory):
        """Test login_redirect uses referer if it contains dashboard."""
        user = user_factory()
        client.force_login(user)

        url = reverse('login_redirect')
        response = client.get(url, HTTP_REFERER='https://example.com/dashboard/my-page')

        assert response.status_code == 302
        assert response.url == '/dashboard/my-page'

    def test_login_redirect_default_from_admin_login(self, client, user_factory):
        """Test login_redirect defaults to /admin/ when coming from admin login."""
        user = user_factory()
        client.force_login(user)

        url = reverse('login_redirect')
        response = client.get(url, HTTP_REFERER='https://example.com/admin/login/')

        assert response.status_code == 302
        assert response.url == '/admin/'

    def test_login_redirect_default_to_dashboard(self, client, user_factory):
        """Test login_redirect defaults to /dashboard/ when no other source."""
        user = user_factory()
        client.force_login(user)

        url = reverse('login_redirect')
        response = client.get(url)

        assert response.status_code == 302
        assert response.url == '/dashboard/'


@pytest.mark.django_db
class TestHelperFunctions:
    """Tests for helper functions in views module."""

    def test_get_next_from_query(self, rf):
        """Test _get_next_from_query helper."""
        request = rf.get('/test', {'next': '/custom'})
        assert views._get_next_from_query(request) == '/custom'

        request = rf.get('/test')
        assert views._get_next_from_query(request) is None

    def test_get_next_from_session(self, rf):
        """Test _get_next_from_session helper."""
        from django.contrib.sessions.middleware import SessionMiddleware

        request = rf.get('/test')
        # Create a proper session
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        request.session['dashboard_next'] = '/session-url'

        result = views._get_next_from_session(request)
        assert result == '/session-url'
        assert 'dashboard_next' not in request.session

        # Test with no session value
        assert views._get_next_from_session(request) is None

    def test_get_next_from_dashboard_flag(self, rf):
        """Test _get_next_from_dashboard_flag helper."""
        from django.contrib.sessions.middleware import SessionMiddleware

        request = rf.get('/test')
        # Create a proper session
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        request.session['dashboard_login'] = True

        result = views._get_next_from_dashboard_flag(request)
        assert result == '/dashboard/'
        assert 'dashboard_login' not in request.session

        # Test with no flag
        assert views._get_next_from_dashboard_flag(request) is None

    def test_get_next_from_social_django(self, rf):
        """Test _get_next_from_social_django helper."""
        from django.contrib.sessions.middleware import SessionMiddleware

        request = rf.get('/test')
        # Create a proper session
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        request.session['next'] = '/social-url'

        result = views._get_next_from_social_django(request)
        assert result == '/social-url'
        assert 'next' not in request.session

        # Test with social_auth_next
        request.session['social_auth_next'] = '/social-auth-url'
        result = views._get_next_from_social_django(request)
        assert result == '/social-auth-url'

        # Test with no session values
        request.session.clear()
        assert views._get_next_from_social_django(request) is None

    def test_get_next_from_referer(self, rf):
        """Test _get_next_from_referer helper."""
        request = rf.get('/test', HTTP_REFERER='https://example.com/dashboard/my-page')
        result = views._get_next_from_referer(request)
        assert result == '/dashboard/my-page'

        # Test with no dashboard in referer
        request = rf.get('/test', HTTP_REFERER='https://example.com/admin/')
        assert views._get_next_from_referer(request) is None

        # Test with no referer
        request = rf.get('/test')
        assert views._get_next_from_referer(request) is None

    def test_get_default_next(self, rf):
        """Test _get_default_next helper."""
        request = rf.get('/test', HTTP_REFERER='https://example.com/admin/login/')
        assert views._get_default_next(request) == '/admin/'

        request = rf.get('/test', HTTP_REFERER='https://example.com/dashboard/')
        assert views._get_default_next(request) == '/dashboard/'

        request = rf.get('/test')
        assert views._get_default_next(request) == '/dashboard/'
