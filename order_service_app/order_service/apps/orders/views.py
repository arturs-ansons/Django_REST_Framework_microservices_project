from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, DatabaseError
from decimal import Decimal, InvalidOperation
import requests, os, logging

from .models import Order
from .serializers import OrderSerializer
from .authentication import ServiceJWTAuthentication

logger = logging.getLogger("orders")

PRODUCT_SERVICE_URL = os.getenv(
    "PRODUCT_SERVICE_URL", "http://product_service:8000/api/products/"
)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = [ServiceJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        user = request.user

        if not user or not user.is_authenticated:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)

        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "quantity must be a positive integer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch product data from Product service
        try:
            headers = {
                "Accept": "application/json",
                "Host": "localhost"  # required for some internal requests
            }
            product_resp = requests.get(
                f"{PRODUCT_SERVICE_URL}{product_id}/",
                headers=headers,
                timeout=5
            )
            product_resp.raise_for_status()

            product_data = product_resp.json()
            price = Decimal(str(product_data.get("price")))
            stock = int(product_data.get("stock", 0))

            if price <= 0:
                raise InvalidOperation

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Product service unavailable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except (TypeError, ValueError, InvalidOperation, KeyError) as e:
            return Response(
                {"error": f"Invalid product price: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_price = price * quantity
        data["user_id"] = user.id
        data["total_price"] = total_price

        # Save order atomically
        try:
            with transaction.atomic():
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return Response(
                {"error": "Database error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response_headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=response_headers)
