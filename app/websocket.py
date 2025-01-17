from fastapi import WebSocket,WebSocketDisconnect,APIRouter
from typing import List


websocket_router=APIRouter()

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = WebSocketManager()


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket=websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected.")
        manager.disconnect(websocket)

