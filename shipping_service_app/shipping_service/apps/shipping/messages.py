from rest_framework import status

VALIDATION_MESSAGES = {
    "shipment": {
        "not_pending_payment": {
            "message": "Only pending shipments can be paid.",
            "status": status.HTTP_400_BAD_REQUEST,
        },
        "not_paid": { 
            "message": "Only paid shipments can be shipped.",
            "status": status.HTTP_400_BAD_REQUEST,
        },
        "already_shipped": {
            "message": "Shipment {shipment_id} has already been shipped.",
            "status": status.HTTP_400_BAD_REQUEST,
        },
        "already_exists": {
            "message": "Shipment for order {order_id} already exists.",
            "status": status.HTTP_400_BAD_REQUEST,
        },
    },
    "order": {
        "service_unavailable": {
            "message": "Order service unavailable: {error}",
            "status": status.HTTP_503_SERVICE_UNAVAILABLE,
        },
        "not_found": {
            "message": "Order {order_id} not found.",
            "status": status.HTTP_404_NOT_FOUND,
        },
        "unexpected_response": {
            "message": "Unexpected response from Order service: {status_code}",
            "status": status.HTTP_502_BAD_GATEWAY,
        },
        "invalid_response": {
            "message": "Invalid response from Order service.",
            "status": status.HTTP_502_BAD_GATEWAY,
        },
        "not_pending": {
            "message": "Order {order_id} is not pending, cannot pay shipment.",
            "status": status.HTTP_400_BAD_REQUEST,
        },
    },
    "success": {
        "shipment_created": {
            "message": "Shipment {shipment_id} created successfully.",
            "status": status.HTTP_201_CREATED,
        },
        "shipment_paid": {
            "message": "Shipment {shipment_id} paid successfully.",
            "status": status.HTTP_200_OK,
        },
        "shipment_shipped": {
            "message": "Shipment {shipment_id} shipped successfully.",
            "status": status.HTTP_200_OK,
        },
        "shipment_appointed": {
            "message": "Shipment {shipment_id} appointed successfully.",
            "status": status.HTTP_200_OK,
        },
    },
}
