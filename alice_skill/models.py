from django.db import models


class User(models.Model):
    alice_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    telegram_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User(alice_id={self.alice_user_id}, tg_id={self.telegram_user_id})"


class LinkToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LinkToken for {self.user}"


class BloodPressureMeasurement(models.Model):
    user_id = models.CharField(max_length=255, db_index=True)
    systolic = models.PositiveIntegerField()
    diastolic = models.PositiveIntegerField()
    pulse = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        pulse_part = f", pulse {self.pulse}" if self.pulse is not None else ""
        return f"{self.systolic}/{self.diastolic}{pulse_part} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
