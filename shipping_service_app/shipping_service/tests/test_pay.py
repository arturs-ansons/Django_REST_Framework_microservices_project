from django.test import TestCase
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from apps.shipping.models import Shipment
from types import SimpleNamespace


class ShipmentViewSetTests(TestCase):
    def setUp(self):
        # Simulate JWT-authenticated users (using your SimpleNamespace logic)
        self.admin_user = SimpleNamespace(id=1, is_authenticated=True, is_admin=True)
        self.normal_user = SimpleNamespace(id=2, is_authenticated=True, is_admin=False)

        # API client
        self.client = APIClient()

        # Create test shipments
        self.shipment1 = Shipment.objects.create(user_id=self.normal_user.id, order_id=101, status="pending")
        self.shipment2 = Shipment.objects.create(user_id=self.normal_user.id, order_id=102, status="paid")

        print("\nInserted Shipments:")
        for s in Shipment.objects.all():
            print(f"id={s.id}, user_id={s.user_id}, order_id={s.order_id}, status={s.status}")

    @patch("apps.shipping.views.publish_event")  # mock RMQ publisher
    @patch("requests.get")  # mock order service
    def test_pay_shipment_changes_status_to_paid(self, mock_get, mock_publish):
        
        # Mock order service to simulate successful response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"id": 101, "status": "pending"}

        # Authenticate as normal user
        self.client.force_authenticate(user=self.normal_user)

        # Call endpoint
        url = f"/api/shipments/{self.shipment1.id}/pay/"
        response = self.client.post(url)

        print(f"\n[test_pay_shipment_changes_status_to_paid] Response Data:\n{response.data}")

        # Refresh shipment from DB
        self.shipment1.refresh_from_db()

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.shipment1.status, "paid")
        self.assertIn("Shipment", response.data["message"])
        mock_publish.assert_called_once()

    
    @patch("requests.get") 
    def test_pay_shipment_fails_if_not_pending(self, mock_get):

        # Mock order service returns confirmed (invalid)
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"id": 101, "status": "confirmed"}

        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(f"/api/shipments/{self.shipment1.id}/pay/")

        print("\n[test_pay_shipment_fails_if_not_pending] Response Data:")
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not pending", response.data["message"])

        updated = Shipment.objects.get(id=self.shipment1.id)
        self.assertEqual(updated.status, "pending")
