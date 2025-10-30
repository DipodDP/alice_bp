from django.contrib import admin
from .models import BloodPressureMeasurement, AliceUser, AccountLinkToken


@admin.register(BloodPressureMeasurement)
class BloodPressureMeasurementAdmin(admin.ModelAdmin):
    list_display = ("user_id", "systolic", "diastolic", "measured_at")
    list_filter = ("user_id", "measured_at")
    search_fields = ("user_id", "systolic", "diastolic")


@admin.register(AliceUser)
class AliceUserAdmin(admin.ModelAdmin):
    list_display = ("alice_user_id", "telegram_user_id", "timezone", "created_at")
    list_filter = ("timezone",)
    search_fields = ("alice_user_id", "telegram_user_id")


@admin.register(AccountLinkToken)
class AccountLinkTokenAdmin(admin.ModelAdmin):
    list_display = ("telegram_user_id", "used", "created_at", "expires_at")
    list_filter = ("used",)
    search_fields = ("telegram_user_id",)
