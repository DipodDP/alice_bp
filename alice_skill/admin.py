from django.contrib import admin
from .models import BloodPressureMeasurement


@admin.register(BloodPressureMeasurement)
class BloodPressureMeasurementAdmin(admin.ModelAdmin):
    list_display = ("user_id", "systolic", "diastolic", "created_at")
    list_filter = ("user_id", "created_at")
    search_fields = ("user_id", "systolic", "diastolic")
