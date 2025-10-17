# shipping/serializers.py
from rest_framework import serializers
from .models import Shipment


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ["id", "user_id", "order_id", "tracking_number", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]