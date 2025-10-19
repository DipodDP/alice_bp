import hmac
from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from ..models import User, LinkToken


class LinkingFlowAPITestCase(APITestCase):
    def setUp(self):
        self.alice_user_id = "TEST_ALICE_USER_ID_12345"
        self.telegram_user_id = "TEST_TELEGRAM_ID_98765"

    def test_initiate_link_success(self):
        """Ensure we can initiate a link and get a token."""
        url = reverse("link-initiate")
        data = {"session": {"user_id": self.alice_user_id}}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("Ваш код для связывания:", response.data["message"])

        # Check database
        self.assertTrue(User.objects.filter(alice_user_id=self.alice_user_id).exists())
        user = User.objects.get(alice_user_id=self.alice_user_id)
        self.assertTrue(LinkToken.objects.filter(user=user).exists())

    def test_initiate_link_missing_user_id(self):
        """Ensure it fails without an alice_user_id."""
        url = reverse("link-initiate")
        data = {"session": {}}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_linking_flow_success(self):
        """Test the complete flow from initiation to completion."""
        # 1. Initiate
        initiate_url = reverse("link-initiate")
        initiate_data = {"session": {"user_id": self.alice_user_id}}
        initiate_response = self.client.post(initiate_url, initiate_data, format="json")
        self.assertEqual(initiate_response.status_code, status.HTTP_201_CREATED)

        message = initiate_response.data["message"]
        token = message.split(": ")[1].split(".")[0]

        # 2. Complete
        complete_url = reverse("link-complete")
        complete_data = {
            "telegram_user_id": self.telegram_user_id,
            "token": token
        }
        complete_response = self.client.post(complete_url, complete_data, format="json")

        self.assertEqual(complete_response.status_code, status.HTTP_200_OK)
        self.assertEqual(complete_response.data["message"], "Аккаунты успешно связаны!")

        # Check database state
        user = User.objects.get(alice_user_id=self.alice_user_id)
        self.assertEqual(user.telegram_user_id, self.telegram_user_id)
        self.assertFalse(LinkToken.objects.filter(user=user).exists())

    def test_complete_link_invalid_token(self):
        """Ensure completing with a bad token fails."""
        url = reverse("link-complete")
        data = {"telegram_user_id": self.telegram_user_id, "token": "XXXX-XXXX"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_link_expired_token(self):
        """Ensure an expired token is rejected and deleted."""
        user = User.objects.create(alice_user_id=self.alice_user_id)
        token_obj = LinkToken.objects.create(
            user=user,
            token_hash="some_hash",
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        url = reverse("link-complete")
        # We need to generate a valid hash for a known token
        raw_token = "EXPIRED1"
        token_hash = hmac.new(settings.SECRET_KEY.encode(), raw_token.encode(), 'sha256').hexdigest()
        token_obj.token_hash = token_hash
        token_obj.save()

        data = {"telegram_user_id": self.telegram_user_id, "token": raw_token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertFalse(LinkToken.objects.filter(id=token_obj.id).exists())

    def test_relink_breaks_old_link(self):
        """Ensure linking a telegram ID to a new alice account breaks the old link."""
        # 1. Create an existing link
        old_alice_user = User.objects.create(alice_user_id="OLD_ALICE_ID", telegram_user_id=self.telegram_user_id)

        # 2. New Alice user initiates a link
        initiate_url = reverse("link-initiate")
        self.client.post(initiate_url, {"session": {"user_id": self.alice_user_id}}, format="json")

        # 3. Get the token for the new user
        new_user = User.objects.get(alice_user_id=self.alice_user_id)
        token_obj = LinkToken.objects.get(user=new_user)

        # We can't get the raw token back in tests, so we cheat a bit by creating a known one
        raw_token = "RELINK01"
        token_hash = hmac.new(settings.SECRET_KEY.encode(), raw_token.encode(), 'sha256').hexdigest()
        token_obj.token_hash = token_hash
        token_obj.save()

        # 4. New user completes link with the SAME telegram ID
        complete_url = reverse("link-complete")
        data = {"telegram_user_id": self.telegram_user_id, "token": raw_token}
        response = self.client.post(complete_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Verify new link and broken old link
        new_user.refresh_from_db()
        old_alice_user.refresh_from_db()

        self.assertEqual(new_user.telegram_user_id, self.telegram_user_id)
        self.assertIsNone(old_alice_user.telegram_user_id)

    def test_status_check_not_linked(self):
        """Ensure status check correctly reports 'not_linked' for unlinked users."""
        User.objects.create(alice_user_id=self.alice_user_id)
        url = reverse("link-status")

        # Check from Alice's side
        alice_data = {"session": {"user_id": self.alice_user_id}}
        response_alice = self.client.post(url, alice_data, format="json")
        self.assertEqual(response_alice.status_code, status.HTTP_200_OK)
        self.assertEqual(response_alice.data["status"], "not_linked")

        # Check from Telegram's side (for a user that doesn't exist yet)
        tg_data = {"telegram_user_id": self.telegram_user_id}
        response_tg = self.client.post(url, tg_data, format="json")
        self.assertEqual(response_tg.status_code, status.HTTP_200_OK)
        self.assertEqual(response_tg.data["status"], "not_linked")

    def test_status_check_linked(self):
        """Ensure status check correctly reports 'linked' for linked users."""
        User.objects.create(alice_user_id=self.alice_user_id, telegram_user_id=self.telegram_user_id)
        url = reverse("link-status")

        # Check from Alice's side
        alice_data = {"session": {"user_id": self.alice_user_id}}
        response_alice = self.client.post(url, alice_data, format="json")
        self.assertEqual(response_alice.status_code, status.HTTP_200_OK)
        self.assertEqual(response_alice.data["status"], "linked")

        # Check from Telegram's side
        tg_data = {"telegram_user_id": self.telegram_user_id}
        response_tg = self.client.post(url, tg_data, format="json")
        self.assertEqual(response_tg.status_code, status.HTTP_200_OK)
        self.assertEqual(response_tg.data["status"], "linked")

    def test_status_check_bad_request(self):
        """Ensure an empty request to status check returns a 400."""
        url = reverse("link-status")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unlink_from_alice(self):
        """Ensure a user can unlink their account from Alice's side."""
        user = User.objects.create(alice_user_id=self.alice_user_id, telegram_user_id=self.telegram_user_id)
        url = reverse("link-unlink")
        data = {"session": {"user_id": self.alice_user_id}}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "unlinked")

        user.refresh_from_db()
        self.assertIsNone(user.telegram_user_id)

    def test_unlink_from_telegram(self):
        """Ensure a user can unlink their account from Telegram's side."""
        user = User.objects.create(alice_user_id=self.alice_user_id, telegram_user_id=self.telegram_user_id)
        url = reverse("link-unlink")
        data = {"telegram_user_id": self.telegram_user_id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "unlinked")

        user.refresh_from_db()
        self.assertIsNone(user.telegram_user_id)

    def test_unlink_already_unlinked(self):
        """Ensure trying to unlink a not-linked account returns a proper status."""
        user = User.objects.create(alice_user_id=self.alice_user_id)
        url = reverse("link-unlink")
        data = {"session": {"user_id": self.alice_user_id}}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "not_linked")
        user.refresh_from_db()
        self.assertIsNone(user.telegram_user_id)

    def test_relink_same_alice_user_to_new_telegram_user(self):
        """Ensure an Alice user can re-link from one Telegram account to another."""
        # 1. Create an initial link to the first Telegram user
        user = User.objects.create(alice_user_id=self.alice_user_id, telegram_user_id="OLD_TELEGRAM_ID")

        # 2. Initiate a new link for the same Alice user
        initiate_url = reverse("link-initiate")
        initiate_response = self.client.post(initiate_url, {"session": {"user_id": self.alice_user_id}}, format="json")
        message = initiate_response.data["message"]
        token = message.split(": ")[1].split(".")[0]

        # 3. Complete the link with the new Telegram ID
        complete_url = reverse("link-complete")
        complete_data = {
            "telegram_user_id": self.telegram_user_id, # This is the new ID
            "token": token
        }
        self.client.post(complete_url, complete_data, format="json")

        # 4. Verify the user is now linked to the new Telegram ID
        user.refresh_from_db()
        self.assertEqual(user.telegram_user_id, self.telegram_user_id)
