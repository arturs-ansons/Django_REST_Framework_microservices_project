import os
import sys
import json
import logging
import django
import pika
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

# ------------------------
# Django setup
# ------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "product_service.settings")

# Initialize Django
django.setup()

from apps.products.models import Product

# ------------------------
# Logging
# ------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# RabbitMQ config
# ------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "shipping_events")

# ------------------------
# Callback function
# ------------------------
def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        event_type = message.get("type") or message.get("event")
        data = message.get("data") or message.get("payload", {})

        logger.info(f"📦 Received event: {event_type} | data={data}")

        if event_type == "shipment.shipped":
            product_id = data.get("product_id")
            quantity = data.get("quantity", 0)

            if not product_id:
                logger.warning("⚠️ Missing product_id in message payload, skipping.")
                return

            try:
                product = Product.objects.get(id=product_id)
                old_qty = product.stock
                product.stock = max(0, product.stock - quantity)
                product.save()
                logger.info(f"✅ Product {product_id} quantity updated: {old_qty} → {product.stock}")

            except Product.DoesNotExist:
                logger.warning(f"⚠️ Product {product_id} not found in DB")
            except Exception as e:
                logger.exception(f"❌ Error updating product {product_id}: {e}")

        else:
            logger.info(f"Ignoring event type: {event_type}")

    except Exception as e:
        logger.exception(f"Failed to process message: {body} | Error: {e}")

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)



# ------------------------
# RabbitMQ consumer
# ------------------------
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=30))
def start_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()

    # Dead-letter queue setup
    dlq_name = f"{RABBITMQ_QUEUE}.dlq"
    channel.queue_declare(queue=dlq_name, durable=True)
    args = {"x-dead-letter-exchange": "", "x-dead-letter-routing-key": dlq_name}

    # Main queue
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True, arguments=args)

    logger.info(f"🚀 Listening to RabbitMQ queue: {RABBITMQ_QUEUE}")

    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
    channel.start_consuming()


# ------------------------
# Main entry
# ------------------------
if __name__ == "__main__":
    start_consumer()
