# shipping/models.py
from django.db import models

class Shipment(models.Model):
    STATUS_CHOICES = [
    ("pending", "Pending"),
    ("paid", "Paid"),
    ("shipped", "Shipped"),
    ("cancelled", "Cancelled"),
]

    order_id = models.IntegerField(unique=True)
    user_id = models.IntegerField(null=True, blank=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shipment {self.id} for Order {self.order_id}"
