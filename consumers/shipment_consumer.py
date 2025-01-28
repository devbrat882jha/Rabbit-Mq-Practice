import pika
import json
from app.models import Order

from consumers.database_connection import Session 
import asyncio
import websockets

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq",port=5672)
)
channel = connection.channel()

channel.exchange_declare(exchange='order', exchange_type='direct', durable=True)
channel.queue_declare(queue='shipment', durable=True)

channel.queue_bind(exchange="order", queue="shipment", routing_key='shipment')

def process_message(ch, method, properties, body):
    asyncio.run(handle_message(body))


async def handle_message( body):
    try:
        session=Session()
        data=json.loads(body)
        print(data,"hello")
        action=data.get('action')
        order_id=int(data.get('order_id'))
        order = session.get(Order, order_id)

        if not order:
            print(f"order {order_id} not found")
            return
        order.status=action
        message=f"Order with {order_id} shipment status has updated to {action}"
        session.commit()
        try:
            async with websockets.connect("ws://localhost:8000/ws") as websocket:
                await websocket.send(message)
                print(f"Message sent to WebSocket: {message}")
        except Exception as websocket_error:
            print(f"WebSocket connection failed: {websocket_error}")
        print(message)
    except Exception as e:
         print(f"Error processing in inventory update : {e}")
         session.rollback()
    finally:
        session.close()
            
        


channel.basic_consume(
    queue="shipment", on_message_callback=process_message, auto_ack=True)



if __name__ == "__main__":
    
    print("Waiting for messages...")
    channel.start_consuming()
