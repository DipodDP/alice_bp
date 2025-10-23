from django.contrib import admin
from .models import BloodPressureMeasurement


@admin.register(BloodPressureMeasurement)
class BloodPressureMeasurementAdmin(admin.ModelAdmin):
    list_display = ("user_id", "systolic", "diastolic", "measured_at")
    list_filter = ("user_id", "measured_at")
    search_fields = ("user_id", "systolic", "diastolic")
