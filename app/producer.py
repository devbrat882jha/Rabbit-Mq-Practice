import pika
import json




def get_rabbitmq_channel():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq",port=5672)
    )
    return connection.channel()

channel = get_rabbitmq_channel()

# Declare exchange and queues
channel.exchange_declare(exchange='order', exchange_type='direct', durable=True)
channel.exchange_declare(exchange='stock_update', exchange_type='direct', durable=True)
queues = ['inventory', 'email', 'shipment']
for queue in queues:
    channel.queue_declare(queue=queue, durable=True)
    channel.queue_bind(exchange="order", queue=queue, routing_key=queue)

channel.queue_declare(queue="stock_update", durable=True)
channel.queue_bind(exchange="stock_update", queue="stock_update", routing_key="stock_update")

def publish_message(exchange, routing_key, message):
    """
    Publishes a message to the given exchange with the specified routing key.
    """
    try:
        if not isinstance(message, str):
            message = json.dumps(message)
        
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message)
        print(f"Message sent to {routing_key}: {message}")
    except Exception as e:
        print(f"Failed to publish message: {e}")




