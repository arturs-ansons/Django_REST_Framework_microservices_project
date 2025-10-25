import os, logging, requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Shipment
from .serializers import ShipmentSerializer
from .messages import VALIDATION_MESSAGES
from .utils import publish_event
from .authentication import ServiceJWTAuthentication
from apps.shipping.permissions import IsJWTAdminUser
from apps.shipping.cache_utils import (
    get_cached_response,
    set_cached_response,
    invalidate_cache_patterns,
)

logger = logging.getLogger(__name__)

# ------------------------
# Environment configuration
# ------------------------
ENVIRONMENT = os.getenv("ENVIRONMENT", "docker")
CONFIG = {
    "development": {
        "ORDER_SERVICE_URL": "http://localhost:8003/api/orders/",
        "USER_SERVICE_URL": "http://localhost:8001/api/users/",
    },
    "docker": {
        "ORDER_SERVICE_URL": "http://order_service:8000/api/orders/",
        "USER_SERVICE_URL": "http://user_service:8000/api/users/",
    },
    "production": {
        "ORDER_SERVICE_URL": "http://orders.mycompany.com/api/orders/",
        "USER_SERVICE_URL": "http://users.mycompany.com/api/users/",
    },
}
ORDER_SERVICE_URL = CONFIG[ENVIRONMENT]["ORDER_SERVICE_URL"]

logger.info(f"[CONFIG] Running in {ENVIRONMENT} environment")
logger.info(f"[CONFIG] ORDER_SERVICE_URL={ORDER_SERVICE_URL}")

# ------------------------
# Helper: Response builder
# ------------------------
def get_response(key, **kwargs):
    data = VALIDATION_MESSAGES
    for part in key.split("."):
        data = data[part]

    message = data["message"].format(**kwargs)
    status_code = data["status"]
    logger.debug(f"Response: key={key}, message='{message}', status={status_code}")
    return Response({"message": message}, status=status_code)


# ------------------------
# ViewSet
# ------------------------
class ShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [ServiceJWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False):
            logger.info(f"Admin user '{user}' requested all shipments.")
            return Shipment.objects.all()
        logger.info(f"User '{user}' requested their own shipments.")
        return Shipment.objects.filter(user_id=user.id)

    # ------------------------
    # Cached endpoints
    # ------------------------
    @action(detail=False, methods=["get"], permission_classes=[IsJWTAdminUser])
    def all_shipments(self, request):

        sort_order = request.query_params.get('sort', '-created_at')
        cached = get_cached_response("all_shipments", request)
        if cached:
            return cached

        shipments = Shipment.objects.all().order_by(sort_order)
        serializer = self.get_serializer(shipments, many=True)
        data = serializer.data
        set_cached_response("all_shipments", request, data)
        return Response(data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_shipments(self, request):
        cached = get_cached_response("my_shipments", request)
        if cached:
            return cached

        shipments = Shipment.objects.filter(user_id=request.user.id)
        serializer = self.get_serializer(shipments, many=True)
        data = serializer.data
        set_cached_response("my_shipments", request, data)
        return Response(data)

    # ------------------------
    # Create shipment from order
    # ------------------------
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def appoint_order(self, request):
        user = request.user
        order_id = request.data.get("order_id")

        if not order_id:
            return get_response("shipment.not_pending_payment")

        headers = {"Authorization": request.headers.get("Authorization", "")}
        if ENVIRONMENT != "production":
            headers["Host"] = "localhost"

        try:
            resp = requests.get(f"{ORDER_SERVICE_URL}{order_id}/", headers=headers, timeout=5)
            if resp.status_code == 404:
                return get_response("order.not_found", order_id=order_id)
            resp.raise_for_status()
            order_data = resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Order service request failed for order {order_id}: {e}")
            return get_response("order.service_unavailable", error=str(e))
        except ValueError:
            logger.error(f"Invalid JSON from order service for order {order_id}")
            return get_response("order.invalid_response")

        if int(order_data.get("user_id")) != int(user.id):
            return Response({"message": "You do not own this order."}, status=403)

        shipment, created = Shipment.objects.get_or_create(
            order_id=order_id,
            defaults={"user_id": user.id, "status": "pending"},
        )

        if not created:
            if shipment.status == "shipped":
                return get_response("shipment.already_shipped", shipment_id=shipment.id)
            return get_response("shipment.already_exists", order_id=order_id)

        serializer = self.get_serializer(shipment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user_id=user.id)

        publish_event("shipment.updated", {"shipment_id": shipment.id, "user_id": user.id})
        invalidate_cache_patterns(["my_shipments", "all_shipments"])

        return get_response("success.shipment_created", shipment_id=shipment.id)

    # ------------------------
    # Payment action
    # ------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def pay(self, request, pk=None):
        shipment = self.get_object()
        user = request.user

        if shipment.user_id != int(user.id):
            raise PermissionDenied("You do not own this shipment.")

        if shipment.status != "pending":
            return get_response("shipment.not_pending_payment")

        shipment.status = "paid"
        shipment.save()



        publish_event("shipment.paid", {"shipment_id": shipment.id, "order_id": shipment.order_id})
        invalidate_cache_patterns(["my_shipments", "all_shipments"])
        return get_response("success.shipment_paid", shipment_id=shipment.id)

    # ------------------------
    # Ship action
    # ------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsJWTAdminUser])
    def ship(self, request, pk=None):
        shipment = self.get_object()

        if shipment.status != "paid":
            return get_response("shipment.not_paid")

        if not shipment.tracking_number:
            shipment.tracking_number = f"TRK{shipment.id:09d}"

        shipment.status = "shipped"
        shipment.save()

        publish_event(
            "shipment.shipped",
            {"shipment_id": shipment.id, "order_id": shipment.order_id, "tracking_number": shipment.tracking_number},
        )
        invalidate_cache_patterns(["my_shipments", "all_shipments"])
        return get_response("success.shipment_shipped", shipment_id=shipment.id)

    # ------------------------
    # Delete action
    # ------------------------
    @action(detail=True, methods=["delete"], permission_classes=[IsJWTAdminUser])
    def delete_shipment(self, request, pk=None):
        shipment = get_object_or_404(Shipment, pk=pk)
        shipment_id = shipment.id
        shipment.delete()

        publish_event("shipment.deleted", {"shipment_id": shipment_id})
        invalidate_cache_patterns(["my_shipments", "all_shipments"])
        return get_response("success.shipment_deleted", shipment_id=shipment_id)

    # ------------------------
    # Update action
    # ------------------------
    @action(detail=True, methods=["patch"], permission_classes=[IsJWTAdminUser])
    def update_shipment(self, request, pk=None):
        shipment = get_object_or_404(Shipment, pk=pk)
        serializer = ShipmentSerializer(shipment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            publish_event("shipment.updated", {"shipment_id": shipment.id})
            invalidate_cache_patterns(["my_shipments", "all_shipments"])
            return get_response("success.shipment_updated", shipment_id=shipment.id)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
