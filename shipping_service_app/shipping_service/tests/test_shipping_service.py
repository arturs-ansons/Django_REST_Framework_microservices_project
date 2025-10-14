# tests/test_shipping_service.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from types import SimpleNamespace
from apps.shipping.models import Shipment

class ShipmentViewSetTests(TestCase):
    def setUp(self):
        # Mock users using SimpleNamespace to match ServiceJWTAuthentication
        self.admin_user = SimpleNamespace(
            id=1,
            is_authenticated=True,
            is_admin=True
        )

        self.normal_user = SimpleNamespace(
            id=2,
            is_authenticated=True,
            is_admin=False
        )

        # Initialize APIClient
        self.client = APIClient()

        # Create shipments
        self.shipment1 = Shipment.objects.create(user_id=self.admin_user.id, order_id=101, status='pending')
        self.shipment2 = Shipment.objects.create(user_id=self.normal_user.id, order_id=102, status='paid')
        self.shipment3 = Shipment.objects.create(user_id=self.normal_user.id, order_id=103, status='pending')

        # Debug print
        print("\nInserted Shipments:")
        for s in Shipment.objects.all():
            print(f"id={s.id}, user_id={s.user_id}, order_id={s.order_id}, status={s.status}")

    def test_my_shipments(self):
        # Authenticate as normal user
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get('/api/shipments/my_shipments/')
        print("\n[test_my_shipments] Response Data:")
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only shipments belonging to normal_user
        self.assertEqual(len(response.data), 2)
        for shipment in response.data:
            self.assertEqual(shipment["user_id"], self.normal_user.id)

    def test_all_shipments_admin_only(self):
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/shipments/all_shipments/')
        print("\n[test_all_shipments_admin_only] Response Data:")
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_all_shipments_forbidden_for_normal_user(self):
        # Authenticate as normal user
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get('/api/shipments/all_shipments/')
        print("\n[test_all_shipments_forbidden_for_normal_user] Response Data:")
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
