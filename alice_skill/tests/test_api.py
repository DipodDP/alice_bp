import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from alice_skill.models import AliceUser, BloodPressureMeasurement

@pytest.mark.django_db
class TestBloodPressureMeasurementAPI:
    def setup_method(self):
        self.client = APIClient()
        User = get_user_model()
        self.django_user = User.objects.create_user(username='test_alice_id', password='testpassword')
        self.alice_user = AliceUser.objects.create(user=self.django_user, alice_user_id='test_alice_id')
        self.measurement = BloodPressureMeasurement.objects.create(
            user_id=self.alice_user.alice_user_id,
            systolic=120,
            diastolic=80,
            pulse=60
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
        other_django_user = User.objects.create_user(username='otheruser', password='testpassword')
        other_alice_user = AliceUser.objects.create(user=other_django_user, alice_user_id='other_alice_id')
        BloodPressureMeasurement.objects.create(
            user_id=other_alice_user.alice_user_id,
            systolic=130,
            diastolic=90,
            pulse=70
        )

        self.client.login(username='otheruser', password='testpassword')
        response = self.client.get('/api/v1/measurements/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['systolic'] == 130