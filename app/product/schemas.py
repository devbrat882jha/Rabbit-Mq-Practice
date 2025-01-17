from pydantic import BaseModel

class ProductBase(BaseModel):
    id:int
    type:str
    price:int
    category:str
    stock_quantity:int
    category:str

class ProductsBase(BaseModel):
    products:ProductBase




    