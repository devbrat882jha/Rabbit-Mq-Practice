from fastapi import APIRouter,HTTPException,status
from app.database import SessionDep
from app.models import User,Product,Order,ProductOrder
from app.user.schemas import UserOrderInput,OrderOutput,UserCreate,ProductOutput
from app.producer import publish_message
from sqlalchemy import select
from fastapi.responses import JSONResponse
from typing import List,Dict
from app.caching import increment_order_count
from sqlalchemy.orm import selectinload
from app.enums import OrderStatus


user_router=APIRouter(prefix="/users",tags=["Users"])


@user_router.post("/create")
async def create_user(user_input:UserCreate,session:SessionDep):
    user=User(email=user_input.email,address=user_input.address)
    session.add(user)
    session.commit()
    data = {"id":None, "user_id": user.id,"email":user.email ,"products":None}
    publish_message(exchange="order", routing_key="email", message={"data":data, 
                                                                    "event": "user_registered"})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message":"User has been created succesfully"})

@user_router.get("/orders/{user_id}")
async def user_orders(user_id: int, session: SessionDep):
    orders = session.exec(
        select(Order).where(Order.user_id == user_id).options(
            selectinload(Order.product_orders).selectinload(ProductOrder.product)
        )
    ).scalars().all()
   
    
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No orders found for the User: {user_id}"
        )

    order_outputs = [
        {
            "order_id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "products": {
                product_order.product.id: {
                    "product_id": product_order.product.id,
                    "type": product_order.product.type,
                    "price": product_order.product.price,
                    "quantity": product_order.quantity  
                }
                for product_order in order.product_orders 
            }
        }
        for order in orders  ]

    return order_outputs

    
@user_router.post("/place/order/{user_id}")
async def place_order(user_id:int,
                      user_input:UserOrderInput,
                      session:SessionDep):
    with session.begin():
        user=session.get(User,user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
        product_ids={int(product.product_id) for product in user_input.products}
   
        products=session.exec(select(Product).where(Product.id.in_(product_ids))).scalars().all()
        if len(product_ids)!=len(products):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="One or More product not found")
        product_map={product.id:product for product in products}
        insufficient_stock=[]
        for item in user_input.products:
            product=product_map.get(item.product_id)
            if  product.is_available is False or item.quantity>product.stock_quantity:
                insufficient_stock.append(item.product_id)
                continue
            else:
                increment_order_count(product_id=product.id)
           
        if insufficient_stock:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for products: {insufficient_stock}"
            )
        order=Order(user_id=user_id)
        session.add(order)
        session.flush()
        products_order=[ProductOrder(product_id=item.product_id,order_id=order.id,quantity=item.quantity ) 
                        for item in user_input.products]
        session.add_all(products_order)
    product_dicts: List[dict] = [
    {
        "product_id": product.product_id,
        "quantity":product.quantity
    }
    for product in user_input.products
]
    order_data = {"id": order.id, "user_id": user_id, "products":product_dicts}
    publish_message(exchange="order", routing_key="inventory", message={"data":order_data, 
                                                                    "event": "placed"})
    publish_message(exchange="order", routing_key="email", message={"data":order_data, 
                                                                    "event": "order_placed"})

    return {"message": f"Order {order.id} placed successfully"}
    


@user_router.get("/order/cancel/{order_id}")
async def get_order_status(user_id:int,order_id:int,session:SessionDep):
    order=session.exec(select(Order).where(Order.id==order_id and Order.user_id==user_id)).scalars().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Order with id : {order_id} not found  ")
    order.status=OrderStatus.Cancelled
    session.commit()
    products=[
        {
        "product_id": product_order.product.id,
        
        "quantity":product_order.quantity
    } for product_order in order.product_orders
    ]
    data = {"id": order.id, "user_id": user_id, "products": products}
    publish_message(exchange="order", routing_key="inventory", message={"data":data,"event": "cancelled"})

    return {"order":order,"message":f"Order with id :{order_id} has been cancelled"}