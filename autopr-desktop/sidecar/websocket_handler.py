import asyncio
import logging
from fastapi import WebSocket

class WebSocketHandler(logging.Handler):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.create_task(self.websocket.send_text(log_entry))
