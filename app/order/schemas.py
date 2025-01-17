from pydantic import BaseModel


class OrderStatus(BaseModel):
    id:int
    status:str

