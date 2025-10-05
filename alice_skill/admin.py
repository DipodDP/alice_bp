from django.contrib import admin
from .models import BloodPressureMeasurement


@admin.register(BloodPressureMeasurement)
class BloodPressureMeasurementAdmin(admin.ModelAdmin):
    list_display = ("systolic", "diastolic", "created_at")
    list_filter = ("created_at",)
    search_fields = ("systolic", "diastolic")
