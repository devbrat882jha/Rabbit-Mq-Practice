import pika
import json
from app.models import Product
from app.database import SessionDep
import asyncio
import websockets
from consumers.database_connection import Session


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost")
)
channel = connection.channel()

channel.exchange_declare(exchange='stock_update', exchange_type='direct', durable=True)
channel.queue_declare(queue='stock_update', durable=True)

channel.queue_bind(exchange="stock_update", queue="stock_update", routing_key='stock_update')

def process_message(ch, method, properties, body):
    asyncio.run(handle_message(body))

async def handle_message( body):
    try:
        session=Session()
        data=json.loads(body)
        print("hehehe")
        action=data.get('action')
        product_id=int(data.get('product_id'))
        quantity=int(data.get('quantity'))
        product=session.get(Product,product_id)
        stock_quantity=0
        if not product:
            print(f"Product {product_id} not found")
            return

        if action=="Add":
            product.stock_quantity += quantity
            stock_quantity=product.stock_quantity
        elif action=="Reduce":
            if product.stock_quantity<quantity:
                print(f"Insufficient stock for product {product_id}")
                return
            product.stock_quantity -= quantity
            stock_quantity=product.stock_quantity
        session.commit()
        message={f"Product : {product.id} stock has updated to : {stock_quantity}"}
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
    queue="stock_update", on_message_callback=process_message, auto_ack=True)


print("Waiting for messages...")
channel.start_consuming()