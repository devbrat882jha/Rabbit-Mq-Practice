from enum import Enum

class ProductType(str,Enum):
    Electronics = "Electronics"
    Fashion = "Fashion"
    Coesmetic="Coesmetic"
    Food="Food"

class OrderStatus(str,Enum):
    Placed="Placed"
    Shipped="Shipped"
    Delivered="Delivered"
    Cancelled="Cancelled"