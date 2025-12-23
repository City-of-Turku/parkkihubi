from rest_framework.routers import DefaultRouter

from ..url_utils import versioned_url
from .event_parking_anonymized import EventParkingAnonymizedViewSet
from .parking_anonymized import ParkingAnonymizedViewSet
from .parking_check_anonymized import ParkingCheckAnonymizedViewSet
from .archived_parking_anonymized import ArchivedParkingAnonymizedViewSet

router = DefaultRouter()

router.register('event_parking_anonymized', EventParkingAnonymizedViewSet, basename='event_parking_anonymized')
router.register('parking_anonymized', ParkingAnonymizedViewSet, basename='parking_anonymized')
router.register('parking_check_anonymized', ParkingCheckAnonymizedViewSet, basename='parking_check_anonymized')
router.register('archived_parking_anonymized', ArchivedParkingAnonymizedViewSet, basename='archived_parking_anonymized')


app_name = 'data'
urlpatterns = [
    versioned_url('v1', router.urls),
]
