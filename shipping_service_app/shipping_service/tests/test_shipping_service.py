from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from types import SimpleNamespace
from django.core.cache import cache
from unittest.mock import patch
from apps.shipping.models import Shipment

class ShipmentViewSetTests(TestCase):
    def setUp(self):
        # Clear cache before each test
        cache.clear()

        # Mock users (ServiceJWTAuthentication-like)
        self.admin_user = SimpleNamespace(id=1, is_authenticated=True, is_admin=True)
        self.normal_user = SimpleNamespace(id=2, is_authenticated=True, is_admin=False)

        self.client = APIClient()

        # Seed test data
        self.shipment1 = Shipment.objects.create(user_id=self.admin_user.id, order_id=101, status='pending')
        self.shipment2 = Shipment.objects.create(user_id=self.normal_user.id, order_id=102, status='paid')
        self.shipment3 = Shipment.objects.create(user_id=self.normal_user.id, order_id=103, status='pending')

    def test_my_shipments(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get('/api/shipments/my_shipments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for shipment in response.data:
            self.assertEqual(shipment["user_id"], self.normal_user.id)

    def test_all_shipments_admin_only(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/shipments/all_shipments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_all_shipments_forbidden_for_normal_user(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get('/api/shipments/all_shipments/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ----------------------------
    # Redis Cache Tests
    # ----------------------------
    def test_my_shipments_cache_set_and_hit(self):
        """First call should set cache, second should hit it."""
        self.client.force_authenticate(user=self.normal_user)

        # Ensure cache is empty
        self.assertEqual(len(cache.keys('*')), 0)

        # First call → should populate cache
        with patch("apps.shipping.cache_utils.logger.info") as mock_log:
            response1 = self.client.get('/api/shipments/my_shipments/')
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
            mock_log.assert_any_call(
                f"[CACHE SET] key=my_shipments_{self.normal_user.id}_"
                + mock_log.call_args_list[-1][0][0].split("_")[-1]
            )

        # Second call → should hit cache
        with patch("apps.shipping.cache_utils.logger.info") as mock_log:
            response2 = self.client.get('/api/shipments/my_shipments/')
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            mock_log.assert_any_call(mock_log.call_args_list[0][0][0])
            found_hit = any("[CACHE HIT]" in str(call) for call in mock_log.call_args_list)
            self.assertTrue(found_hit, "Cache HIT should be logged")

        # Responses should be identical
        self.assertEqual(response1.data, response2.data)

    def test_cache_invalidation_after_update(self):
        """Cache should be invalidated after updating a shipment."""
        self.client.force_authenticate(user=self.admin_user)

        # Prime the cache
        self.client.get('/api/shipments/all_shipments/')
        self.assertTrue(any("all_shipments" in key for key in cache.keys('*')))

        # Update shipment → should invalidate cache
        response = self.client.patch(
            f'/api/shipments/{self.shipment1.id}/update_shipment/',
            {"status": "paid"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cache should now be cleared
        self.assertEqual(len(cache.keys('*')), 0)
