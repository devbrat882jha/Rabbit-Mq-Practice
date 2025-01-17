from sqlmodel import SQLModel,Field,Relationship
from app.enums import ProductType,OrderStatus
from typing import List
from datetime import datetime




class User(SQLModel,table=True):
    id:int=Field(default=None,primary_key=True)
    email:str
    address:str
    orders:list["Order"]=Relationship(back_populates="user")

class ProductOrder(SQLModel,table=True):
    id:int=Field(default=None,primary_key=True)
    product_id:int=Field(foreign_key="product.id")
    order_id:int=Field(foreign_key="order.id")
    quantity: int = Field(default=1)
    product:'Product'=Relationship(back_populates="product_orders")
    order:'Order'=Relationship(back_populates="product_orders")

class Product(SQLModel,table=True):
    id:int=Field(default=None,primary_key=True)
    type:ProductType
    category:str
    price:int
    stock_quantity: int = Field(default=0)
    is_available: bool = Field(default=True)
    order: list["Order"] = Relationship(back_populates="product",link_model=ProductOrder)
    product_orders: list["ProductOrder"] = Relationship(back_populates="product")






class Order(SQLModel,table=True):
    id:int=Field(default=None,primary_key=True)
    user_id:int=Field(foreign_key="user.id",ondelete="CASCADE")
    status: OrderStatus = Field(default="Placed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user:User=Relationship(back_populates="orders")
    product:list["Product"]=Relationship(back_populates="order",link_model=ProductOrder)
    product_orders: list["ProductOrder"] = Relationship(back_populates="order")


