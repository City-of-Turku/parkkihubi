import csv

from django.contrib import admin
from django.http import HttpResponse


class ReadOnlyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [x.name for x in obj._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class WithAreaField:
    area_scale = 1000000

    def area(self, instance):
        if not instance.geom:
            return ''
        assert self.area_scale in [1000000, 1]
        unit = 'km\u00b2' if self.area_scale == 1000000 else 'm\u00b2'
        return '{area:.1f} {unit}'.format(
            area=instance.geom.area / self.area_scale, unit=unit)


def export_as_csv(admin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{admin.model._meta.model_name}.csv"'
    writer = csv.writer(response)
    all_fields = [field.name for field in admin.model._meta.fields]
    # Fields can be left out with extra argument
    exclude_fields = getattr(admin, 'exclude_csv_fields', [])
    field_names = [f for f in all_fields if f not in exclude_fields]
    writer.writerow(field_names)

    for obj in queryset:
        row = [getattr(obj, field) for field in field_names]
        writer.writerow(row)

    return response
