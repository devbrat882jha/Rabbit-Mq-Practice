import redis
import json
from app.database import SessionDep
from sqlmodel import select
from app.models import Product

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def increment_order_count(product_id:int):
    r.zincrby('product_order_count',1,product_id)
    r.expire('product_order_counts', 3600)

def get_top_placed_products(n:int):
    top_products=r.zrevrange('product_order_count',0,n-1,withscores=True)
    return top_products


    
def get_cached_products(n:int,session:SessionDep):
    top_product_ids_with_scores = get_top_placed_products(n)
    top_product_ids = [product_id for product_id, _ in top_product_ids_with_scores]

    cached_products=[]
    missing_product_ids=[]

    for product_id in top_product_ids:
        product_data = r.get(f"product:{product_id}")
        if product_data:
            cached_products.append(json.loads(product_data))
        else:
            missing_product_ids.append(int(product_id))

    if missing_product_ids:
        products_db=session.exec(select(Product).where(Product.id.in_(missing_product_ids))).all()
        for product in products_db:
            product_data = {
                "id": product.id,
                
                "stock_quantity": product.stock_quantity,
                "price": product.price,
                "category":product.category
            }
            r.setex(f"product:{product.id}",3600,json.dumps(product_data))
            cached_products.append(product_data)
    return {"products":cached_products[:n]}


def get_cached_product(product_id:str,session:SessionDep):
    product_data=r.get(product_id)
    if product_data:
        return {"product":json.loads(product_data)}
    product=session.get(Product,int(product_id))
    product_data = {
        "id": product.id,
         "type":product.type,
        "stock_quantity": product.stock_quantity,
        "price": product.price,
        "category":product.category

    }
    r.setex(f"product:{product.id}", 3600, json.dumps(product_data))  
    return product_data
    