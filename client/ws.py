import asyncio
from websockets.asyncio.client import connect
from websockets import exceptions
import queue

messages = queue.Queue()


async def listen():
    async with connect("ws://localhost:8000/ws/") as websocket:
        print("WebSocket connection established.")

        while True:
            try:
                message = await websocket.recv()
                print("Received message: " + message)
                messages.put(message)

            except exceptions.ConnectionClosedError:

                break

            except Exception as e:
                print(f"[ERROR] WebSocket error: {e}")
                break


def start_listening():
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        pass
