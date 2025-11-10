import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from alice_skill.models import AliceUser, BloodPressureMeasurement
from django.urls import reverse
from unittest.mock import patch
from django.utils import timezone


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_check_healthy(self):
        client = APIClient()
        url = reverse('health-check')
        response = client.get(url)
        assert response.status_code == 200
        assert response.data == {'status': 'healthy', 'database': 'connected'}

    @patch('django.db.connection.ensure_connection')
    def test_health_check_unhealthy(self, mock_ensure_connection):
        mock_ensure_connection.side_effect = Exception('DB is down')
        client = APIClient()
        url = reverse('health-check')
        response = client.get(url)
        assert response.status_code == 503
        assert response.data['status'] == 'unhealthy'
        assert response.data['database'] == 'disconnected'


@pytest.mark.django_db
class TestBloodPressureMeasurementAPI:
    def setup_method(self):
        self.client = APIClient()
        User = get_user_model()
        self.django_user = User.objects.create_user(
            username='test_alice_id', password='testpassword'
        )
        self.alice_user = AliceUser.objects.create(
            user=self.django_user, alice_user_id='test_alice_id'
        )
        self.measurement = BloodPressureMeasurement.objects.create(
            user=self.alice_user, systolic=120, diastolic=80, pulse=60
        )

    def test_get_measurements_authenticated(self):
        self.client.login(username='test_alice_id', password='testpassword')
        response = self.client.get('/api/v1/measurements/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['systolic'] == 120

    def test_get_measurements_unauthenticated(self):
        response = self.client.get('/api/v1/measurements/')
        assert response.status_code == 403

    def test_get_measurements_other_user(self):
        User = get_user_model()
        other_django_user = User.objects.create_user(
            username='otheruser', password='testpassword'
        )
        other_alice_user = AliceUser.objects.create(
            user=other_django_user, alice_user_id='other_alice_id'
        )
        BloodPressureMeasurement.objects.create(
            user=other_alice_user, systolic=130, diastolic=90, pulse=70
        )

        self.client.login(username='otheruser', password='testpassword')
        response = self.client.get('/api/v1/measurements/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['systolic'] == 130

    def test_get_measurements_as_bot(self):
        from django.conf import settings  # Import settings to get API_TOKEN

        User = get_user_model()
        bot_target_django_user = User.objects.create_user(
            username='bot_target_user', password='testpassword'
        )
        bot_target_alice_user = AliceUser.objects.create(
            user=bot_target_django_user, alice_user_id='bot_target_alice_id'
        )
        BloodPressureMeasurement.objects.create(
            user=bot_target_alice_user, systolic=140, diastolic=95, pulse=80
        )

        # Make a request as a bot
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + settings.API_TOKEN)
        response = self.client.get(
            f'/api/v1/measurements/?user_id={bot_target_alice_user.alice_user_id}'
        )
        self.client.credentials()  # Clear credentials

        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['systolic'] == 140
        assert response.data['results'][0]['user'] == bot_target_alice_user.pk

    def test_get_measurements_with_date_filter(self):
        from django.conf import settings
        from datetime import datetime, timedelta

        # Create some measurements with different dates
        now = timezone.now()
        BloodPressureMeasurement.objects.create(
            user=self.alice_user,
            systolic=1,
            diastolic=1,
            measured_at=now - timedelta(days=1),
        )
        BloodPressureMeasurement.objects.create(
            user=self.alice_user,
            systolic=2,
            diastolic=2,
            measured_at=now - timedelta(days=5),
        )
        BloodPressureMeasurement.objects.create(
            user=self.alice_user,
            systolic=3,
            diastolic=3,
            measured_at=now - timedelta(days=10),
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + settings.API_TOKEN)

        # Filter for the last 7 days
        start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')

        response = self.client.get(
            f'/api/v1/measurements/?user_id={self.alice_user.alice_user_id}&created_at__gte={start_date}&created_at__lte={end_date}'
        )

        self.client.credentials()

        assert response.status_code == 200
        assert len(response.data['results']) == 3
        assert response.data['results'][0]['systolic'] == 120
        assert response.data['results'][1]['systolic'] == 1
        assert response.data['results'][2]['systolic'] == 2
