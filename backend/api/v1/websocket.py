from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)
        logger.info(f"WebSocket подключен к {room}")
    
    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)
    
    async def broadcast(self, message: dict, room: str):
        if room in self.active_connections:
            for connection in self.active_connections[room]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@router.websocket("/connect/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"message": data}, room)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
