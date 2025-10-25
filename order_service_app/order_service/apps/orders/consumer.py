import os,sys,json,logging,django,pika
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

# ------------------------
# Django setup
# ------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "order_service.settings")

# Initialize Django
django.setup()

from apps.orders.models import Order


# ------------------------
# Logging
# ------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# RabbitMQ config
# ------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")

# ------------------------
# Callback function
# ------------------------
def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        event_type = message.get("type")
        data = message.get("data", {})

        order_id = data.get("order_id")
        if not order_id:
            logger.warning("No order_id in payload, skipping")
            return

        try:
            order = Order.objects.get(id=order_id)

            if event_type == "shipment.paid":
                order.status = "paid"
                order.save()
                logger.info(f"✅ Order {order_id} status updated to 'paid'")

            elif event_type == "shipment.shipped":
                order.status = "shipped"
                order.save()
                logger.info(f"✅ Order {order_id} status updated to 'shipped'")

            else:
                logger.info(f"Ignoring event type: {event_type}")

        except Order.DoesNotExist:
            logger.warning(f"Order {order_id} not found in DB")

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

    # Ensure queues exist
    dlq_name = f"{RABBITMQ_QUEUE}.dlq"
    channel.queue_declare(queue=dlq_name, durable=True)
    args = {"x-dead-letter-exchange": "", "x-dead-letter-routing-key": dlq_name}
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True, arguments=args)

    logger.info(f"Listening to RabbitMQ queue: {RABBITMQ_QUEUE}")

    # Start consuming
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
    channel.start_consuming()


# ------------------------
# Main entry
# ------------------------
if __name__ == "__main__":
    start_consumer()
