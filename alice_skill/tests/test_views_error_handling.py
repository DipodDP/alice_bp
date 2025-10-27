from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from django.conf import settings

from alice_skill.messages import GenerateLinkTokenViewMessages


class ViewErrorHandlingTest(APITestCase):
    authentication_classes = []
    permission_classes = []

    def setUp(self):
        self.generate_link_token_url = reverse("link-generate-token")
        self.unlink_url = reverse("link-unlink")
        self.telegram_user_id = 12345
        settings.API_TOKEN = "test-api-token" # Set a dummy API token for testing

    def test_generate_link_token_view_exception_handling(self):
        """
        Tests that GenerateLinkTokenView handles exceptions during token generation.
        """
        # Mock generate_link_token to raise an exception
        with patch('alice_skill.views.generate_link_token', side_effect=Exception("Test exception")) as mock_generate_link_token:
            response = self.client.post(self.generate_link_token_url, {
                "telegram_user_id": self.telegram_user_id
            }, format="json", HTTP_AUTHORIZATION=f"Token {settings.API_TOKEN}")

            mock_generate_link_token.assert_called_once_with(telegram_user_id=self.telegram_user_id)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data["status"], "error")
            self.assertEqual(response.data["message"], GenerateLinkTokenViewMessages.FAIL)

    @patch('alice_skill.views.User.objects.filter')
    def test_unlink_view_exception_handling(self, mock_user_filter):
        """
        Tests that UnlinkView handles exceptions during unlinking.
        """
        # Mock the .first() call to raise an exception
        mock_user_filter.return_value.first.side_effect = Exception("Test exception")

        response = self.client.post(self.unlink_url, {
            "telegram_user_id": self.telegram_user_id
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["message"], "Test exception") # The view returns the exception message directly



