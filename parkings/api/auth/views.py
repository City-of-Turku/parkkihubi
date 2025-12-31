from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def check_auth(request):
    """
    Check if the user is authenticated.
    Returns 200 with user info if authenticated, 401 if not.
    """
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'username': request.user.username,
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'authenticated': False,
        }, status=status.HTTP_401_UNAUTHORIZED)


def dashboard_login(request):
    """
    Custom login view for dashboard that preserves the 'next' parameter.
    Stores 'next' in session and redirects to admin login with the next parameter.
    """
    next_url = request.GET.get('next')

    # Store the next URL in session so it can be retrieved after OAuth callback
    if next_url:
        request.session['dashboard_next'] = next_url
        request.session.modified = True
        # Also pass it as a query parameter to admin login so helusers can pick it up
        return redirect(f'/admin/login/?next={next_url}')

    # If no next URL, assume user wants to go to dashboard
    # Store a flag in session to indicate dashboard login
    request.session['dashboard_login'] = True
    request.session.modified = True

    # If user is already authenticated, redirect them directly
    if request.user.is_authenticated:
        return login_redirect(request)

    # Otherwise, redirect to admin login (which will show the login form)
    return redirect('/admin/login/')


def _get_next_from_query(request):
    """Get next URL from query string."""
    return request.GET.get('next')


def _get_next_from_session(request):
    """Get next URL from session and clear it."""
    next_url = request.session.get('dashboard_next')
    if next_url:
        del request.session['dashboard_next']
        request.session.modified = True
    return next_url


def _get_next_from_dashboard_flag(request):
    """Get next URL from dashboard login flag."""
    if request.session.get('dashboard_login'):
        del request.session['dashboard_login']
        request.session.modified = True
        return '/dashboard/'
    return None


def _get_next_from_social_django(request):
    """Get next URL from social_django session data."""
    next_url = request.session.get('next') or request.session.get('social_auth_next')
    if next_url and 'next' in request.session:
        del request.session['next']
        request.session.modified = True
    return next_url


def _get_next_from_referer(request):
    """Get next URL from HTTP referer if it contains dashboard path."""
    referer = request.META.get('HTTP_REFERER')
    if referer and '/dashboard' in referer:
        parsed = urlparse(referer)
        if '/dashboard' in parsed.path:
            return parsed.path
    return None


def _get_default_next(request):
    """Get default next URL based on referer."""
    referer = request.META.get('HTTP_REFERER', '')
    if '/admin/login' in referer:
        return '/admin/'
    return '/dashboard/'


@login_required
def login_redirect(request):
    """
    Redirect after successful login.
    Checks for 'next' parameter in query string, session, or social_django session data.
    """
    # Try different sources in order of priority
    next_url = (
        _get_next_from_query(request) or
        _get_next_from_session(request) or
        _get_next_from_dashboard_flag(request) or
        _get_next_from_social_django(request) or
        _get_next_from_referer(request) or
        _get_default_next(request)
    )

    return redirect(next_url)
