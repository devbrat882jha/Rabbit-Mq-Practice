from pydantic import BaseModel
from typing import List

class UserCreate(BaseModel):
    email:str
    address:str


class ProductInput(BaseModel):
    product_id:int
    quantity:int

class UserOrderInput(BaseModel):
    products:List[ProductInput]

class ProductOutput(BaseModel):
    product_id:int
    type:str
    price:int
    stock_quantity:int
    is_available:bool




class OrderOutput(BaseModel):
    order_id:int
    user_id:int
    status:str
    products:List[ProductOutput]

