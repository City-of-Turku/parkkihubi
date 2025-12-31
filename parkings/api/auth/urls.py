from django.urls import re_path

from parkings.api.auth import views

from ..url_utils import versioned_url

app_name = 'auth'
urlpatterns = [
    # Token checking based on Django authentication
    versioned_url('v1', [
        re_path(r'^check/$', views.check_auth, name='check'),
    ]),
]
