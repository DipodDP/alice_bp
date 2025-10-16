from django.db import models


class BloodPressureMeasurement(models.Model):
    user_id = models.CharField(max_length=255, db_index=True)
    systolic = models.PositiveIntegerField()
    diastolic = models.PositiveIntegerField()
    pulse = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        pulse_part = f", pulse {self.pulse}" if self.pulse is not None else ""
        return f"{self.systolic}/{self.diastolic}{pulse_part} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"