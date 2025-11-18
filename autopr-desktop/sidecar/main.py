import asyncio
import logging
import uvicorn
from fastapi import FastAPI, WebSocket
from autopr.engine import AutoPREngine
from .websocket_handler import WebSocketHandler

app = FastAPI()

# Get the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/status")
async def get_status():
    engine = AutoPREngine()
    return engine.get_status()

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    handler = WebSocketHandler(websocket)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    engine = AutoPREngine(log_handler=handler)

    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        logger.removeHandler(handler)
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
