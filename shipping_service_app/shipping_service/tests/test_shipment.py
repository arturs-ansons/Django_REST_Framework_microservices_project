from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from apps.shipping.models import Shipment

User = get_user_model()


class ShipmentViewSetTests(TestCase):
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(username='admin1', password='pass', is_staff=True)
        self.normal_user = User.objects.create_user(username='user1', password='pass')

        self.client = APIClient()

        # Create some shipments
        self.shipment1 = Shipment.objects.create(user_id=self.admin_user.id, order_id=101, status='pending')
        self.shipment2 = Shipment.objects.create(user_id=self.normal_user.id, order_id=102, status='paid')
        self.shipment3 = Shipment.objects.create(user_id=self.normal_user.id, order_id=103, status='pending')

        print("\nInserted Shipments:")
        for s in Shipment.objects.all():
            print(f"id={s.id}, user_id={s.user_id}, order_id={s.order_id}, status={s.status}")

    @patch("requests.get")
    @patch("apps.shipping.views.publish_event")  # Mock RMQ event publisher
    def test_appoint_order_creates_new_shipment(self, mock_publish, mock_get):
        """User can appoint an order to create a shipment."""
        # Mock order service response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "id": 999,
            "status": "paid",
            "user_id": self.normal_user.id
        }

        # Authenticate as the normal user (from JWT behavior)
        self.client.force_authenticate(user=self.normal_user)

        # Simulate API call
        response = self.client.post("/api/shipments/appoint_order/", {"order_id": 999}, format="json")

        print("\n[test_appoint_order_creates_new_shipment] Response Data:")
        print(response.data)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Shipment.objects.filter(order_id=999).exists())

        # Ensure RMQ event was published
        mock_publish.assert_called_once()
