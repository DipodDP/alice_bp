from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


class AliceUser(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    alice_user_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True, db_index=True
    )
    telegram_user_id_hash = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'AliceUser(user={self.user}, alice_user_id={self.alice_user_id}, telegram_user_id_hash={self.telegram_user_id_hash})'


class BloodPressureMeasurementQuerySet(models.QuerySet):
    def for_user(self, request):
        """
        Filters the queryset based on the user type and query parameters from the request.
        """
        user = request.user
        is_bot_request = getattr(request, 'is_bot', False)

        # Case 1: Request is from the bot
        if is_bot_request:
            user_id = request.query_params.get('user_id')
            if user_id:
                return self.filter(user__alice_user_id=user_id)
            return self.none()

        # Case 2: User is a superuser
        if user.is_superuser:
            user_id = request.query_params.get('user_id')
            if user_id:
                return self.filter(user__alice_user_id=user_id)
            return self

        # Case 3: Regular authenticated user
        if user.is_authenticated:
            try:
                alice_user = AliceUser.objects.select_related('user').get(user=user)
                return self.filter(user=alice_user)
            except AliceUser.DoesNotExist:
                return self.none()

        # Case 4: Unauthenticated user (and not a bot)
        return self.none()


class BloodPressureMeasurement(models.Model):
    user = models.ForeignKey(
        AliceUser, on_delete=models.CASCADE, related_name='measurements'
    )
    systolic = models.IntegerField()
    diastolic = models.IntegerField()
    pulse = models.IntegerField(null=True, blank=True)
    measured_at = models.DateTimeField(default=timezone.now)

    objects = BloodPressureMeasurementQuerySet.as_manager()

    class Meta:
        ordering = ['-measured_at']
        indexes = [
            # Composite index for filtering by user and ordering by measured_at
            models.Index(fields=['user', '-measured_at'], name='bp_user_time_idx'),
        ]

    def __str__(self):
        return f'BP: {self.systolic}/{self.diastolic} at {self.measured_at.strftime("%Y-%m-%d %H:%M")}'


class AccountLinkToken(models.Model):
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    telegram_user_id_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Account Link Token'
        verbose_name_plural = 'Account Link Tokens'

    def __str__(self):
        return (
            f'Token for Telegram User {self.telegram_user_id_hash} (Used: {self.used})'
        )
