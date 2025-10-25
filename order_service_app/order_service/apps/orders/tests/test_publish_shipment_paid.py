import sys
import os
import time
import json
import pika
import django

# ------------------------
# Setup Django environment
# ------------------------
# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "order_service.settings")
django.setup()

from apps.orders.models import Order

# ------------------------
# RabbitMQ config
# ------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = "shipping_events_test"


def publish_shipment_paid(shipment_id, order_id):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()

    # Ensure queue exists
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    message = json.dumps({
        "type": "shipment.paid",
        "data": {
            "shipment_id": shipment_id,
            "order_id": order_id
        }
    })

    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )

    connection.close()
    print(f"✅ Published shipment.paid event for order {order_id}")


def test_order_status(order_id):
    order = Order.objects.get(id=order_id)
    print(f"Order {order_id} status: {order.status}")
    return order.status


if __name__ == "__main__":
    TEST_ORDER_ID = 28
    TEST_SHIPMENT_ID = 28

    # Step 1: Publish event
    publish_shipment_paid(TEST_SHIPMENT_ID, TEST_ORDER_ID)

    # Step 2: Wait for consumer to process
    print("⏳ Waiting 5 seconds for consumer to process...")
    time.sleep(5)

    # Step 3: Check order status
    status = test_order_status(TEST_ORDER_ID)
    assert status == "paid", f"❌ Test failed, order status is {status}"
    print("✅ Test passed: Order status updated to 'paid'")
