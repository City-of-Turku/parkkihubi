from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
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


@login_required
def login_redirect(request):
    """
    Redirect after successful login.
    Checks for 'next' parameter in query string, session, or social_django session data.
    """
    # Check for 'next' in query string first (from OAuth callback)
    next_url = request.GET.get('next')

    # Check our custom session key for dashboard redirects
    if not next_url:
        next_url = request.session.get('dashboard_next')
        if next_url:
            # Clear it from session after use
            del request.session['dashboard_next']
            request.session.modified = True

    # Check if user came from dashboard login (without explicit next parameter)
    if not next_url and request.session.get('dashboard_login'):
        next_url = '/dashboard/'
        # Clear the flag after use
        del request.session['dashboard_login']
        request.session.modified = True

    # If not in query string, check social_django's session data
    # social_django stores the next URL in session with key 'next'
    if not next_url:
        # Check various possible session keys that social_django might use
        next_url = request.session.get('next') or request.session.get('social_auth_next')
        if next_url and 'next' in request.session:
            del request.session['next']
            request.session.modified = True

    # If still no next URL, check referer for dashboard path
    if not next_url and request.META.get('HTTP_REFERER'):
        referer = request.META['HTTP_REFERER']
        if '/dashboard' in referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            if '/dashboard' in parsed.path:
                next_url = parsed.path

    # Default to dashboard if no next URL found (most common case for dashboard users)
    # Only default to admin if explicitly coming from admin login
    if not next_url:
        if request.META.get('HTTP_REFERER') and '/admin/login' in request.META.get('HTTP_REFERER', ''):
            next_url = '/admin/'
        else:
            next_url = '/dashboard/'

    return redirect(next_url)

