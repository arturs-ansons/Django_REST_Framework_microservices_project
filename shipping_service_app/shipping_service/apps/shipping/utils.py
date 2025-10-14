import json, pika, logging
from tenacity import retry, stop_after_attempt, wait_exponential
import os

logger = logging.getLogger(__name__)

# RabbitMQ config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "shipping_events")

# Retry up to 5 times with exponential backoff (2s → 30s)
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=30))
def publish_event(event_type, payload):
    """Publish event to RabbitMQ with retry, logging, and DLQ."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()

    # ------------------------
    # Declare Dead Letter Queue (DLQ)
    # ------------------------
    dlq_name = f"{RABBITMQ_QUEUE}.dlq"
    channel.queue_declare(queue=dlq_name, durable=True)

    # ------------------------
    # Declare Main Queue with DLQ Binding
    # ------------------------
    args = {
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": dlq_name,
    }
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True, arguments=args)

    # ------------------------
    # Publish Message
    # ------------------------
    message = json.dumps({"type": event_type, "data": payload})
    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),  # Persistent
    )

    connection.close()

    logger.info(
        f"✅ Published event: type={event_type}, payload={payload}, queue={RABBITMQ_QUEUE}"
    )
