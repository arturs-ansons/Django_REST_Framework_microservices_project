import os, logging, requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Shipment
from .serializers import ShipmentSerializer
from .messages import VALIDATION_MESSAGES
from .utils import publish_event
from .authentication import ServiceJWTAuthentication
from apps.shipping.permissions import IsJWTAdminUser
from django.shortcuts import get_object_or_404


# Elastic logging
logger = logging.getLogger(__name__)


# Environment configuration
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


def get_response(key, **kwargs):
    data = VALIDATION_MESSAGES
    for part in key.split("."):
        data = data[part]

    message = data["message"].format(**kwargs)
    status_code = data["status"]

    logger.debug(f"Response: key={key}, message='{message}', status={status_code}, kwargs={kwargs}")

    return Response({"message": message}, status=status_code)


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
    

    @action(detail=False, methods=["get"], permission_classes=[IsJWTAdminUser])
    def all_shipments(self, request):
        logger.info(f"Admin '{request.user}' requested all shipments.")
        shipments = Shipment.objects.all()
        serializer = self.get_serializer(shipments, many=True)
        return Response(serializer.data)
    

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_shipments(self, request):
        logger.info(f"User '{request.user}' requested their shipments.")
        shipments = Shipment.objects.filter(user_id=request.user.id)
        serializer = self.get_serializer(shipments, many=True)
        return Response(serializer.data)
    
    
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def appoint_order(self, request):
        user = request.user
        order_id = request.data.get("order_id")

        if not order_id:
            return get_response("shipment.not_pending_payment")

        headers = {"Authorization": request.headers.get("Authorization", "")}
        if ENVIRONMENT != "production":
            headers["Host"] = "localhost"

        # Fetch order from Orders service
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

        # Ownership check
        if int(order_data.get("user_id")) != int(user.id):
            logger.warning(f"User {user.id} does not own order {order_id}")
            return Response({"message": "You do not own this order."}, status=403)

        # Get or create shipment
        shipment, created = Shipment.objects.get_or_create(
            order_id=order_id,
            defaults={"user_id": user.id, "status": "pending"}
        )

        if not created:
            # Prevent appointing a shipment that already exists
            if shipment.status == "shipped":
                return get_response("shipment.already_shipped", shipment_id=shipment.id)
            return get_response("shipment.already_exists", order_id=order_id)

        # Update shipment with any additional data
        serializer = self.get_serializer(shipment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user_id=user.id)

        logger.info(f"Shipment {shipment.id} appointed for Order {order_id} by User {user.id}")
        publish_event("shipment.updated", {"shipment_id": shipment.id, "user_id": user.id})

        return get_response("success.shipment_created", shipment_id=shipment.id)




    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def pay(self, request,pk=None):
        shipment = self.get_object()
        user = request.user
        logger.info(f"User '{user}' attempting to pay for shipment ID={shipment.id}.")

        # Ownership check
        if shipment.user_id != int(user.id):
            logger.warning(f"Permission denied: User '{user}' does not own shipment ID={shipment.id}.")
            raise PermissionDenied("You do not own this shipment.")

        if shipment.status != "pending":
            logger.warning(f"Shipment ID={shipment.id} not pending. Current status={shipment.status}.")
            return get_response("shipment.not_pending_payment")

        headers = {"Authorization": request.headers.get("Authorization", "")}
        if ENVIRONMENT != "production":
            headers["Host"] = "localhost"

        order_id = shipment.order_id
        try:
            logger.debug(f"Fetching order {order_id} from {ORDER_SERVICE_URL}")
            resp = requests.get(f"{ORDER_SERVICE_URL}{order_id}/", headers=headers, timeout=5)
            resp.raise_for_status()
            order_data = resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Order service request failed for order {order_id}: {e}")
            return get_response("order.service_unavailable", error=str(e))
        except ValueError:
            logger.error(f"Invalid JSON response from order service for order {order_id}")
            return get_response("order.invalid_response")

        if order_data.get("status") != "pending":
            logger.warning(f"Order {order_id} is not pending. Current status={order_data.get('status')}")
            return get_response("order.not_pending", order_id=order_id)

        shipment.status = "paid"
        shipment.save()
        publish_event("shipment.paid", {"shipment_id": shipment.id, "order_id": order_id})
        logger.info(f"Shipment ID={shipment.id} marked as paid (order ID={order_id}).")

        return get_response("success.shipment_paid", shipment_id=shipment.id)

    @action(detail=True, methods=["post"], permission_classes=[IsJWTAdminUser])
    def ship(self, request, pk=None):
        shipment = self.get_object()
        logger.info(f"Admin '{request.user}' shipping shipment ID={shipment.id}.")

        if shipment.status != "paid":
            logger.warning(f"Shipment ID={shipment.id} cannot be shipped. Status={shipment.status}")
            return get_response("shipment.not_paid")

        if not shipment.tracking_number:
            shipment.tracking_number = f"TRK{shipment.id:09d}"

        shipment.status = "shipped"
        shipment.save()

        publish_event(
            "shipment.shipped",
            {"shipment_id": shipment.id, "tracking_number": shipment.tracking_number}
        )

        logger.info(
            f"Shipment ID={shipment.id} shipped successfully with tracking={shipment.tracking_number}."
        )

        return get_response("success.shipment_shipped", shipment_id=shipment.id)
    
    @action(detail=True, methods=["delete"], url_path="delete", permission_classes=[IsJWTAdminUser])
    def delete_shipment(self, request, pk=None):
        shipment = get_object_or_404(Shipment, pk=pk)
        shipment_id = shipment.id
        shipment.delete()

        logger.info(f"Shipment deleted: id={shipment_id}, user={request.user}")

        publish_event("shipment.deleted", {"shipment_id": shipment_id})

        return get_response("success.shipment_deleted", shipment_id=shipment_id)

    @action(detail=True, methods=["patch"], url_path="update-shipment", permission_classes=[IsJWTAdminUser])
    def update_shipment(self, request, pk=None):
        shipment = get_object_or_404(Shipment, pk=pk)
        serializer = ShipmentSerializer(shipment, data=request.data, partial=True)  # partial=True allows any subset
        if serializer.is_valid():
            serializer.save()

            logger.info(
                f"Shipment updated: id={shipment.id}, updated_fields={list(request.data.keys())}, user={request.user}"
            )

            return get_response("success.shipment_updated", shipment_id=shipment.id, shipment=serializer.data)
        else:
            logger.warning(
                f"Shipment update failed: id={pk}, errors={serializer.errors}, user={request.user}"
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
