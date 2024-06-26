import pytz
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from rest_framework import mixins, serializers, viewsets

from parkings.models import EnforcementDomain, EventArea, EventParking
from parkings.models.constants import WGS84_SRID
from parkings.models.utils import get_closest_area

from ..common import ParkingException
from .permissions import IsOperator

DEFAULT_DOMAIN_CODE = EnforcementDomain.get_default_domain_code()


class OperatorAPIEventParkingSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField(source='get_state')
    domain = serializers.SlugRelatedField(
        slug_field='code', queryset=EnforcementDomain.objects.all(),
        default=EnforcementDomain.get_default_domain)
    event_area_id = serializers.CharField(max_length=50, required=False)

    class Meta:
        model = EventParking
        fields = (
            'id', 'created_at', 'modified_at',
            'location',
            'registration_number',
            'time_start', 'time_end',
            'status',
            'domain',
            'event_area_id',
        )

        # these are needed because by default a PUT request that does not contain some optional field
        # works the same way as PATCH would, ie. not updating that field to null on the target object,
        # which seems wrong. see https://github.com/encode/django-rest-framework/issues/3648
        extra_kwargs = {
            'location': {'default': None},
            'time_end': {'default': None},
        }

    def __init__(self, *args, **kwargs):
        super(OperatorAPIEventParkingSerializer, self).__init__(*args, **kwargs)
        self.fields['time_start'].timezone = pytz.utc
        self.fields['time_end'].timezone = pytz.utc

        initial_data = getattr(self, 'initial_data', None)
        if (initial_data and not initial_data.get('event_area_id', False) and not initial_data.get('location', False)
                and (self.context['request'].method == 'POST' or self.context['request'].method == 'PUT')):
            raise serializers.ValidationError(
                _('"location" inside an event area or "event_area_id" parameter is required'))

    def validate(self, data):
        if self.instance and (now() - self.instance.created_at) > settings.PARKKIHUBI_TIME_EVENT_PARKINGS_EDITABLE:
            if set(data.keys()) != {'time_end'}:
                raise ParkingException(
                    _('Grace period has passed. Only "time_end" can be updated via PATCH.'),
                    code='grace_period_over',
                )

        if self.instance:
            # a partial update might be missing one or both of the time fields
            time_start = data.get('time_start', self.instance.time_start)
            time_end = data.get('time_end', self.instance.time_end)
        else:
            time_start = data['time_start']
            time_end = data['time_end']

        if time_end is not None and time_start > time_end:
            raise serializers.ValidationError(_('"time_start" cannot be after "time_end".'))

        return data

    def create(self, validated_data):
        domain = validated_data.get('domain', None)
        event_area = None
        event_area_id = validated_data.get('event_area_id', None)
        if event_area_id:
            event_area = EventArea.objects.filter(id=event_area_id, domain=domain).first()
            if not event_area:
                raise serializers.ValidationError(
                    _('EventArea with event_area_id: {} does not exist in domain {}.').format(event_area_id, domain))

        if not event_area:
            location = validated_data.get('location', None)
            if location and not location.srid:
                location.srid = WGS84_SRID
            event_area = get_closest_area(location, domain, area_model=EventArea)

        if not event_area and location:
            raise serializers.ValidationError(
                _('No event area found in given location {} and domain {}').format(location, domain))

        if not event_area.is_active:
            raise serializers.ValidationError(_('EventArea {} is not active').format(str(event_area.id)))

        validated_data['event_area_id'] = getattr(event_area, 'id', None)

        return EventParking.objects.create(**validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        field = 'event_area'
        if getattr(instance, field) is not None:
            representation['event_area_id'] = getattr(instance, field).id
        else:
            representation['event_area_id'] is None
        return representation


class OperatorAPIEventParkingPermission(IsOperator):
    def has_object_permission(self, request, view, obj):
        """
        Allow operators to modify only their own parkings.
        """
        return request.user.operator == obj.operator


class OperatorAPIEventParkingViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                                     viewsets.GenericViewSet):
    permission_classes = [OperatorAPIEventParkingPermission]
    queryset = EventParking.objects.order_by('time_start')
    serializer_class = OperatorAPIEventParkingSerializer

    def perform_create(self, serializer):
        serializer.save(operator=self.request.user.operator)

    def get_queryset(self):
        return super().get_queryset().filter(operator=self.request.user.operator)
