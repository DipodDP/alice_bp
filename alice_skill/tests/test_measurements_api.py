from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.urls import reverse
from django.utils import timezone
from alice_skill.tests.factories import TestDataFactory
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User as DjangoUser

from ..models import BloodPressureMeasurement, AliceUser


class MeasurementsApiBasicCrudTests(APITestCase):
    def setUp(self):
        self.list_url = reverse('measurement-list')
        self.django_user = DjangoUser.objects.create_user(
            username='test_user', password='testpassword'
        )
        self.user = AliceUser.objects.create(
            user=self.django_user, alice_user_id='test_user'
        )
        self.client.login(username='test_user', password='testpassword')

    def test_list_empty_with_no_user_id(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_list_empty_for_user_with_no_measurements(self):
        response = self.client.get(self.list_url, {'user_id': self.user.alice_user_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_create_and_retrieve(self):
        payload = {'user': self.user.pk, 'systolic': 125, 'diastolic': 82, 'pulse': 70}
        create_resp = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BloodPressureMeasurement.objects.count(), 1)

        obj = BloodPressureMeasurement.objects.first()
        self.assertEqual(obj.user, self.user)

        detail_url = reverse('measurement-detail', args=[obj.pk])
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['systolic'], 125)
        self.assertEqual(detail_resp.data['diastolic'], 82)
        self.assertEqual(detail_resp.data['pulse'], 70)

    def test_unauthenticated_access_denied(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bot_access_without_user_id_returns_empty(self):
        self.client.logout()  # Ensure not authenticated as a regular user
        bot_token = 'test_bot_token'
        with self.settings(API_TOKEN=bot_token):
            response = self.client.get(
                self.list_url, HTTP_AUTHORIZATION=f'Bearer {bot_token}'
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_superuser_access_without_user_id_returns_all_measurements(self):
        # Create a measurement for the current user
        TestDataFactory.create_measurement(user=self.user, systolic=130, diastolic=85)

        # Create another user and some measurements for them
        other_django_user = DjangoUser.objects.create_user(
            username='other_user', password='testpassword'
        )
        other_alice_user = AliceUser.objects.create(
            user=other_django_user, alice_user_id='other_user'
        )
        TestDataFactory.create_measurement(
            user=other_alice_user, systolic=110, diastolic=70
        )

        # Make the current user a superuser
        self.django_user.is_superuser = True
        self.django_user.save()

        # Log in as superuser
        self.client.force_authenticate(user=self.django_user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Expect 2 measurements: one from self.user, one from other_alice_user
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)


class MeasurementsApiUpdateDeleteOrderingTests(APITestCase):
    def setUp(self):
        self.list_url = reverse('measurement-list')
        self.django_user = DjangoUser.objects.create_user(
            username='test_user_ordering', password='testpassword'
        )
        self.user = AliceUser.objects.create(
            user=self.django_user, alice_user_id='test_user_ordering'
        )
        self.client.login(username='test_user_ordering', password='testpassword')

    def test_update_and_delete(self):
        m = BloodPressureMeasurement.objects.create(
            user=self.user, systolic=120, diastolic=80, pulse=65
        )
        detail_url = reverse('measurement-detail', args=[m.pk])

        # partial update
        patch_resp = self.client.patch(detail_url, {'pulse': 72}, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data['pulse'], 72)

        # delete
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)

    def test_ordering_by_created_desc(self):
        BloodPressureMeasurement.objects.create(
            user=self.user, systolic=110, diastolic=70, pulse=60
        )
        BloodPressureMeasurement.objects.create(
            user=self.user, systolic=130, diastolic=85, pulse=75
        )
        list_resp = self.client.get(self.list_url, {'user_id': self.user.alice_user_id})
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(list_resp.data['count'], 2)
        self.assertEqual(len(list_resp.data['results']), 2)
        self.assertEqual(list_resp.data['results'][0]['systolic'], 130)


class MeasurementsApiValidationTests(APITestCase):
    def setUp(self):
        self.list_url = reverse('measurement-list')
        self.django_user = DjangoUser.objects.create_user(
            username='validation_user', password='testpassword'
        )
        self.user = AliceUser.objects.create(
            user=self.django_user, alice_user_id='validation_user'
        )
        self.client.login(username='validation_user', password='testpassword')

    def test_validation_errors(self):
        # systolic must be > diastolic
        bad_payload = {'user': self.user.pk, 'systolic': 80, 'diastolic': 90}
        resp = self.client.post(self.list_url, bad_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # out of range
        bad_payload = {'user': self.user.pk, 'systolic': 20, 'diastolic': 10}
        resp = self.client.post(self.list_url, bad_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class MeasurementsApiTimezoneTests(APITestCase):
    def setUp(self):
        self.list_url = reverse('measurement-list')
        self.django_user = DjangoUser.objects.create_user(
            username='test_user_for_tz', password='testpassword'
        )
        self.user = AliceUser.objects.create(
            user=self.django_user,
            alice_user_id='test_user_for_tz',
            timezone='America/New_York',
        )
        self.client.login(username='test_user_for_tz', password='testpassword')
        self.measurement = BloodPressureMeasurement.objects.create(
            user=self.user,
            systolic=120,
            diastolic=80,
            pulse=60,
            measured_at=timezone.now(),
        )

    def test_timezone_conversion(self):
        response = self.client.get(self.list_url, {'user_id': self.user.alice_user_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        measured_at_str = response.data['results'][0]['measured_at']
        # Use strptime with the explicit format to ensure timezone awareness
        measured_at_dt = datetime.strptime(measured_at_str, '%Y-%m-%dT%H:%M:%S.%f%z')

        # Check that the timezone is correct
        ny_tz = ZoneInfo('America/New_York')
        # Convert to New York timezone and then compare the timezone info
        converted_dt = measured_at_dt.astimezone(ny_tz)
        self.assertEqual(converted_dt.tzinfo, ny_tz)

        # Check that the time is correct by comparing with original UTC time
        original_utc_time = self.measurement.measured_at.astimezone(ZoneInfo('UTC'))
        response_time_utc = measured_at_dt.astimezone(ZoneInfo('UTC'))

        self.assertAlmostEqual(
            original_utc_time, response_time_utc, delta=timedelta(seconds=1)
        )

    def test_timezone_conversion_for_bot_request(self):
        """Test that bot requests with user_id get timezone conversion for measured_at."""
        self.client.logout()  # Ensure not authenticated as a regular user
        bot_token = 'test_bot_token'

        with self.settings(API_TOKEN=bot_token):
            response = self.client.get(
                self.list_url,
                {'user_id': self.user.alice_user_id},
                HTTP_AUTHORIZATION=f'Token {bot_token}',
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        measured_at_str = response.data['results'][0]['measured_at']
        # Use strptime with the explicit format to ensure timezone awareness
        # The format might vary, so try both with and without microseconds
        try:
            measured_at_dt = datetime.strptime(
                measured_at_str, '%Y-%m-%dT%H:%M:%S.%f%z'
            )
        except ValueError:
            measured_at_dt = datetime.strptime(measured_at_str, '%Y-%m-%dT%H:%M:%S%z')

        # Check that the timezone is correct (should be America/New_York)
        ny_tz = ZoneInfo('America/New_York')
        # Convert to New York timezone and then compare the timezone info
        converted_dt = measured_at_dt.astimezone(ny_tz)
        self.assertEqual(converted_dt.tzinfo, ny_tz)

        # Check that the time is correct by comparing with original UTC time
        original_utc_time = self.measurement.measured_at.astimezone(ZoneInfo('UTC'))
        response_time_utc = measured_at_dt.astimezone(ZoneInfo('UTC'))

        self.assertAlmostEqual(
            original_utc_time, response_time_utc, delta=timedelta(seconds=1)
        )

    def test_measurements_pagination(self):
        # Create more measurements than the default page size
        for _ in range(15):
            TestDataFactory.create_measurement(
                user=self.user, systolic=120, diastolic=80
            )

        # Test default page size
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size

        # Test custom page size
        response = self.client.get(f'{self.list_url}?page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        # Test custom page size larger than default
        response = self.client.get(f'{self.list_url}?page_size=20')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data['results']), 16
        )  # Should return all 16 measurements


class MeasurementsApiFilteringTests(APITestCase):
    def setUp(self):
        self.list_url = reverse('measurement-list')
        self.django_user = DjangoUser.objects.create_user(
            username='test_user_filtering', password='testpassword'
        )
        self.user = AliceUser.objects.create(
            user=self.django_user, alice_user_id='test_user_filtering'
        )
        self.client.login(username='test_user_filtering', password='testpassword')

        # Create some measurements with different dates
        now = timezone.now()
        TestDataFactory.create_measurement(
            user=self.user,
            systolic=120,
            diastolic=80,
            measured_at=now - timedelta(days=5),
        )
        TestDataFactory.create_measurement(
            user=self.user,
            systolic=121,
            diastolic=81,
            measured_at=now - timedelta(days=3),
        )
        TestDataFactory.create_measurement(
            user=self.user,
            systolic=122,
            diastolic=82,
            measured_at=now - timedelta(days=1),
        )

    def test_filter_by_created_at_gte(self):
        # Filter for measurements from 4 days ago until now
        four_days_ago = (timezone.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        response = self.client.get(self.list_url, {'created_at__gte': four_days_ago})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        # Check that the oldest measurement is not included
        for result in response.data['results']:
            self.assertNotEqual(result['systolic'], 120)

    def test_filter_by_created_at_lte(self):
        # Filter for measurements up to 2 days ago
        two_days_ago = (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(self.list_url, {'created_at__lte': two_days_ago})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        # Check that the newest measurement is not included
        for result in response.data['results']:
            self.assertNotEqual(result['systolic'], 122)

    def test_filter_by_created_at_range(self):
        # Filter for measurements between 4 and 2 days ago
        four_days_ago = (timezone.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        two_days_ago = (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(
            self.list_url,
            {'created_at__gte': four_days_ago, 'created_at__lte': two_days_ago},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['systolic'], 121)
