from fastapi import FastAPI,Request
import time
from app.order.router import order_router
from app.product.router import product_router
from app.user.router import user_router
from app.websocket import websocket_router

app=FastAPI()


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(order_router)
app.include_router(product_router)
app.include_router(websocket_router)


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    print(f"Time take top process request: {str(process_time)} ")
    return response
