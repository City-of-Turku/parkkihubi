from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path

from parkings.api.auth import urls as auth_urls
from parkings.api.auth import views as auth_views
from parkings.api.data import urls as data_urls
from parkings.api.enforcement import urls as enforcement_urls
from parkings.api.monitoring import urls as monitoring_urls
from parkings.api.operator import urls as operator_urls
from parkings.api.public import urls as public_urls

urlpatterns = [
    re_path(r'^auth/', include(auth_urls)),
    # Custom login view for dashboard that preserves 'next' parameter
    # Must come before social_django catch-all to handle /login/ specifically
    re_path(r'^login/$', auth_views.dashboard_login, name='dashboard_login'),
    # Custom login redirect to handle 'next' parameter after Tunnistamo login
    re_path(r'^login-redirect/$', auth_views.login_redirect, name='login_redirect'),
]

if getattr(settings, 'PARKKIHUBI_PUBLIC_API_ENABLED', False):
    urlpatterns.append(re_path(r'^public/', include(public_urls)))

if getattr(settings, 'PARKKIHUBI_MONITORING_API_ENABLED', False):
    urlpatterns.append(re_path(r'^monitoring/', include(monitoring_urls)))

if getattr(settings, 'PARKKIHUBI_OPERATOR_API_ENABLED', False):
    urlpatterns.append(re_path(r'^operator/', include(operator_urls)))

if getattr(settings, 'PARKKIHUBI_ENFORCEMENT_API_ENABLED', False):
    urlpatterns.append(re_path(r'^enforcement/', include(enforcement_urls)))

if getattr(settings, 'PARKKIHUBI_DATA_API_ENABLED', False):
    urlpatterns.append(re_path(r'^data/', include(data_urls)))

urlpatterns.extend([
    re_path(r'^admin/', admin.site.urls),
    re_path(r'', include('social_django.urls', namespace='social')),
    re_path(r'', include('helusers.urls')),
])
