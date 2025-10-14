from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id','user_id', 'product_id', 'quantity', 'total_price', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

