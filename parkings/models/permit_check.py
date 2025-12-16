from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import JSONField
from django.utils.translation import gettext_lazy as _

from parkings.models import Permit
from parkings.models.constants import WGS84_SRID
from parkings.models.mixins import AnonymizableRegNumQuerySet
from parkings.models.utils import _format_coordinates


class PermitCheckQuerySet(AnonymizableRegNumQuerySet, models.QuerySet):
    def created_before(self, time):
        return self.filter(created_at__lt=time)


class PermitCheck(models.Model):
    """
    A performed check of allowance of a parking permit.

    An instance is stored for each checking action done via the
    check_permit endpoint.  Each instance records the query parameters
    and the results of the check.
    """
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_("time created"))
    performer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False,
        verbose_name=_("performer"),
        help_text=_("User who performed the check"))

    # Query parameters
    time = models.DateTimeField(verbose_name=_("time"))
    time_overridden = models.BooleanField(
        verbose_name=_("time was overridden"))
    registration_number = models.CharField(
        max_length=20, verbose_name=_("registration number"))
    location = gis_models.PointField(
        srid=WGS84_SRID, verbose_name=_("location"))

    # Results
    result = JSONField(
        blank=True, encoder=DjangoJSONEncoder, verbose_name=_("result"))
    allowed = models.BooleanField(verbose_name=_("permit was allowed"))
    found_permit = models.ForeignKey(
        Permit, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name=_("found permit"))

    objects = PermitCheckQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = _("parking permit check")
        verbose_name_plural = _("parking permit checks")

    def __str__(self):
        location_data = (self.result.get("location")
                         if isinstance(self.result, dict) else None) or {}
        return "[{t}] {time}{o} {coords} Z{zone}/{area} {regnum}: {ok}".format(
            t=self.created_at,
            time=self.time,
            o="*" if self.time_overridden else " ",
            coords=_format_coordinates(self.location),
            zone=location_data.get("payment_zone") or "-",
            area=location_data.get("permit_area") or "-",
            regnum=self.registration_number,
            ok="OK" if self.allowed else "x")
