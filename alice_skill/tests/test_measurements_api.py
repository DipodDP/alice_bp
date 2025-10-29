from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import BloodPressureMeasurement, User


class MeasurementsApiBasicCrudTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("measurement-list")
        self.user = User.objects.create(alice_user_id="test_user")

    def test_list_empty_with_no_user_id(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_empty_for_user_with_no_measurements(self):
        response = self.client.get(self.list_url, {"user_id": self.user.alice_user_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_and_retrieve(self):
        payload = {"user_id": self.user.alice_user_id, "systolic": 125, "diastolic": 82, "pulse": 70}
        create_resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BloodPressureMeasurement.objects.count(), 1)

        obj = BloodPressureMeasurement.objects.first()
        self.assertEqual(obj.user_id, self.user.alice_user_id)

        detail_url = reverse("measurement-detail", args=[obj.pk])
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data["systolic"], 125)
        self.assertEqual(detail_resp.data["diastolic"], 82)
        self.assertEqual(detail_resp.data["pulse"], 70)


class MeasurementsApiUpdateDeleteOrderingTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("measurement-list")
        self.user = User.objects.create(alice_user_id="test_user_ordering")

    def test_update_and_delete(self):
        m = BloodPressureMeasurement.objects.create(user_id=self.user.alice_user_id, systolic=120, diastolic=80, pulse=65)
        detail_url = reverse("measurement-detail", args=[m.pk])

        # partial update
        patch_resp = self.client.patch(detail_url, {"pulse": 72}, format="json")
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data["pulse"], 72)

        # delete
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)

    def test_ordering_by_created_desc(self):
        BloodPressureMeasurement.objects.create(user_id=self.user.alice_user_id, systolic=110, diastolic=70, pulse=60)
        BloodPressureMeasurement.objects.create(user_id=self.user.alice_user_id, systolic=130, diastolic=85, pulse=75)
        list_resp = self.client.get(self.list_url, {"user_id": self.user.alice_user_id})
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data), 2)
        self.assertEqual(list_resp.data[0]["systolic"], 130)
        self.assertEqual(list_resp.data[1]["systolic"], 110)


class MeasurementsApiValidationTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("measurement-list")

    def test_validation_errors(self):
        # systolic must be > diastolic
        bad_payload = {"user_id": "u", "systolic": 80, "diastolic": 90}
        resp = self.client.post(self.list_url, bad_payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # out of range
        bad_payload = {"user_id": "u", "systolic": 20, "diastolic": 10}
        resp = self.client.post(self.list_url, bad_payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class MeasurementsApiTimezoneTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("measurement-list")
        self.user = User.objects.create(
            alice_user_id="test_user_for_tz",
            timezone="America/New_York"
        )
        self.measurement = BloodPressureMeasurement.objects.create(
            user_id=self.user.alice_user_id,
            systolic=120,
            diastolic=80,
            pulse=60,
            measured_at=timezone.now()
        )

    def test_timezone_conversion(self):
        response = self.client.get(self.list_url, {"user_id": self.user.alice_user_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        measured_at_str = response.data[0]["measured_at"]
        measured_at_dt = datetime.fromisoformat(measured_at_str)

        # Check that the timezone is correct
        ny_tz = ZoneInfo("America/New_York")
        self.assertEqual(measured_at_dt.tzinfo.utcoffset(None), ny_tz.utcoffset(datetime.now()))

        # Check that the time is correct by comparing with original UTC time
        original_utc_time = self.measurement.measured_at.astimezone(ZoneInfo("UTC"))
        response_time_utc = measured_at_dt.astimezone(ZoneInfo("UTC"))

        self.assertAlmostEqual(original_utc_time, response_time_utc, delta=timedelta(seconds=1))