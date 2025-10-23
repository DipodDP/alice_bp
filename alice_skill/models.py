from django.db import models
from django.utils import timezone


class User(models.Model):
    alice_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    telegram_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User(alice_id={self.alice_user_id}, tg_id={self.telegram_user_id})"


class BloodPressureMeasurement(models.Model):
    user_id = models.CharField(max_length=255, db_index=True)
    systolic = models.IntegerField()
    diastolic = models.IntegerField()
    pulse = models.IntegerField(null=True, blank=True)
    measured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-measured_at']

    def __str__(self):
        return f"BP: {self.systolic}/{self.diastolic} at {self.measured_at.strftime('%Y-%m-%d %H:%M')}"


class AccountLinkToken(models.Model):
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    telegram_user_id = models.BigIntegerField(db_index=True)
    token_word_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Account Link Token"
        verbose_name_plural = "Account Link Tokens"

    def __str__(self):
        return f"Token for Telegram User {self.telegram_user_id} (Used: {self.used})"

