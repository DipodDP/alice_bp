from django.contrib import admin
from .models import BloodPressureMeasurement, AliceUser, AccountLinkToken


@admin.register(BloodPressureMeasurement)
class BloodPressureMeasurementAdmin(admin.ModelAdmin):
    list_display = ("user", "systolic", "diastolic", "measured_at")
    list_filter = ("user", "measured_at")
    search_fields = ("user__alice_user_id", "systolic", "diastolic")


@admin.register(AliceUser)
class AliceUserAdmin(admin.ModelAdmin):
    list_display = ("alice_user_id", "telegram_user_id_hash", "timezone", "created_at")
    list_filter = ("timezone",)
    search_fields = ("alice_user_id", "telegram_user_id_hash")


@admin.register(AccountLinkToken)
class AccountLinkTokenAdmin(admin.ModelAdmin):
    list_display = ("telegram_user_id_hash", "used", "created_at", "expires_at")
    list_filter = ("used",)
    search_fields = ("telegram_user_id_hash",)
