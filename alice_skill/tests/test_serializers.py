from django.test import TestCase
from ..models import AliceUser
from ..serializers import BloodPressureMeasurementSerializer


class BloodPressureSerializerValidationTests(TestCase):
    def setUp(self):
        self.user = AliceUser.objects.create(alice_user_id='u')

    def test_range_validation(self):
        ser = BloodPressureMeasurementSerializer(data={"systolic": 20, "diastolic": 10})
        self.assertFalse(ser.is_valid())
        ser = BloodPressureMeasurementSerializer(data={"systolic": 120, "diastolic": 300})
        self.assertFalse(ser.is_valid())

    def test_relational_validation(self):
        ser = BloodPressureMeasurementSerializer(data={"systolic": 80, "diastolic": 90})
        self.assertFalse(ser.is_valid())
        ser = BloodPressureMeasurementSerializer(data={"user": self.user.pk, "systolic": 120, "diastolic": 80})
        self.assertTrue(ser.is_valid())

