from consumers.database_connection import Session 
from app.models import Product
from sqlalchemy import select
import pika
import json






connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq",port=5672)
)
channel = connection.channel()

channel.exchange_declare(exchange='order', exchange_type='direct', durable=True)
channel.queue_declare(queue='inventory', durable=True)
channel.queue_bind(exchange="order", queue="inventory", routing_key='inventory')


def callback(ch, method, properties, body):
    session = Session()  
    try:
        order_details = json.loads(body)
        products = order_details.get('data', {}).get("products", [])
        event = order_details.get('event')
        product_ids = [product['product_id'] for product in products]

        result = session.execute(select(Product).where(Product.id.in_(product_ids)))
        product_instances = result.scalars().all()
        product_map = {product.id: product for product in product_instances}

        for product in products:
            product_instance = product_map.get(product['product_id'])
            if not product_instance:
                print(f"Product {product['product_id']} not found")
                continue

            quantity = product['quantity']
            if event == "cancelled":
                product_instance.stock_quantity += quantity
                if not product_instance.is_available and product_instance.stock_quantity > 0:
                    product_instance.is_available = True
            elif event == "placed":
                if product_instance.stock_quantity < quantity:
                    product_instance.is_available = False
                    continue
                product_instance.stock_quantity -= quantity

      
        session.commit()
        print(f"Stock updated successfully for products: {product_ids}")
    except Exception as e:
        print(f"Error processing inventory update: {e}")
        session.rollback()
    finally:
        session.close()


channel.basic_consume(
    queue="inventory", on_message_callback=callback, auto_ack=True
)


if __name__ == "__main__":
    
    print("Waiting for messages...")
    channel.start_consuming()
