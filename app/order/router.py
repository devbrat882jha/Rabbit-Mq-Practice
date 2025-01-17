from fastapi import APIRouter,HTTPException,Query,status
from app.database import SessionDep
from sqlmodel import select
from app.models import Order
from app.order.schemas import OrderStatus
from app.enums import OrderStatus
from app.producer import publish_message
import json

order_router=APIRouter(prefix="/order",tags=['Order'])

@order_router.get("/status")
async def get_orders_status(session: SessionDep):
    orders = session.exec(select(Order)).all()
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")

    result = [{"id": order.id, "status": order.status} for order in orders]
    return result



@order_router.get("/update/status/{order_id}")
async def update_order_status(
    order_id:int,
    action:OrderStatus=Query(...),
):
  
    data={"order_id":order_id,"action":action}
    publish_message(exchange="order",routing_key="shipment",message=json.dumps(data))
    return {"message":"Status has been published"}
    





