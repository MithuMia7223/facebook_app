import asyncio
from websockets.asyncio.client import connect
import queue

messages = queue.Queue()


async def listen():
    async with connect("ws://localhost:8000/ws/") as websocket:
        print("WebSocket connection established.")

        while True:
            message = await websocket.recv()
            print("Received message: " + message)
            messages.put(message)


def start_listening():
    asyncio.run(listen())
