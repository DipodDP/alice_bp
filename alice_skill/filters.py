import django_filters
from .models import BloodPressureMeasurement


class BloodPressureMeasurementFilter(django_filters.FilterSet):
    """
    FilterSet for filtering BloodPressureMeasurement by date range.
    """

    created_at__gte = django_filters.DateFilter(
        field_name='measured_at', lookup_expr='date__gte'
    )
    created_at__lte = django_filters.DateFilter(
        field_name='measured_at', lookup_expr='date__lte'
    )

    class Meta:
        model = BloodPressureMeasurement
        fields = ['created_at__gte', 'created_at__lte']
