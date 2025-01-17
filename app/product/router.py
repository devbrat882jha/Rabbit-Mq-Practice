from fastapi import APIRouter,HTTPException,status,Query
from app.database import SessionDep
from app.product.schemas import ProductBase,ProductsBase
from app.models import Product
from sqlmodel import select
from app.caching import get_cached_products,get_cached_product
from app.producer import publish_message
from enum import Enum
import json


product_router=APIRouter(prefix="/products",tags=["Products"])


@product_router.post("/create")
async def create_product(product_input:ProductBase,session:SessionDep):
    existing_product=session.exec(
                                select(Product).where(
                                Product.category==product_input.category.lower())
                                ).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product of type '{product_input.type}' already exists."
        )

    new_product = Product(
            type=product_input.type,
            price=product_input.price,
            stock_quantity=product_input.stock_quantity,
            category=product_input.category
        )
    session.add(new_product)
    session.commit()
    return {"messaage":"Product has been created successfully","data":new_product}
        

@product_router.get("/list")
async def list_products(
    session: SessionDep,
    page: int = 1,  # Current page number
    per_page: int = 10,  # Number of products per page
    n: int = 5,  # Number of top products to cache
):
    cached_products_data=get_cached_products(n=n,session=session)
    cached_products=cached_products_data["products"]
    cached_product_ids=[]
    if cached_products:
        for cached_product in cached_products:
            cached_product_ids.append(int(cached_product['id']))

    total_cached = len(cached_products)
    remaining_offset = max(0, (page - 1) * per_page - total_cached)
    remaining_limit = max(0, per_page - total_cached)


    if remaining_limit > 0:
        remaining_products=session.exec(
            select(Product)
            .where(Product.id.not_in(cached_product_ids)) 
            .offset(remaining_offset)
            .limit(remaining_limit)
        ).all()

    remaining_products_data = [
        {
            "id": product.id,
             "type":product.type,
            "stock_quantity": product.stock_quantity,
            "price": product.price,
            "category": product.category,
        }
        for product in remaining_products
    ]
    total_products=cached_products+remaining_products_data

    return {
        "products": total_products, 
        "page": page,
        "per_page": per_page,
        "total_cached": total_cached,
        "total_products_returned": len(total_products),
    }

    

@product_router.get("/detail/{product_id}",response_model=ProductBase)
async def get_product_detail(product_id:int,session:SessionDep):
    product=get_cached_product(str(str(product_id)),session=session)
    if product:
    
        return product
    product_db=session.get(Product,product_id)
    return product_db

class Action(str, Enum):
    add = "Add"
    reduce = "Reduce"

@product_router.put("/update/stock/{product_id}")
async def update_stock(
        product_id:int,
        quantity:int,
        action: Action = Query(...),
):
    message = {
        "event": "update_inventory",
        "product_id": product_id,
        "quantity": quantity,
        "action": action  
    }
    publish_message(exchange="stock_update", routing_key="stock_update", message=json.dumps(message))
    return {"message": "Stock update event published"}
    
    




