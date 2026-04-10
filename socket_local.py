from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Websocket Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" />
  </head>
  <body>
    <div class="container mt-3">
      <h1>FastAPI WebSocket Chat</h1>
      <form action="" onsubmit="sendMessage(event)">
        <input type="text" class="form-control" id="messageText" autocomplete="off" placeholder="Type a message..." />
        <button type="submit" class="btn btn-outline-primary mt-2">Send</button>
      </form>
      <ul id="messages" class="mt-4 list-group"></ul>
    </div>
    <script>
      var ws = new WebSocket("ws://localhost:8000/ws");

      ws.onmessage = function(event) {
        var messages = document.getElementById("messages");
        var item = document.createElement("li");
        item.className = "list-group-item";
        item.textContent = event.data;
        messages.appendChild(item);
      };

      ws.onclose = function(event) {
        var messages = document.getElementById("messages");
        var item = document.createElement("li");
        item.className = "list-group-item list-group-item-warning";
        item.textContent = "Connection closed.";
        messages.appendChild(item);
      };

      function sendMessage(event) {
        event.preventDefault();
        var input = document.getElementById("messageText");
        if (!input.value) return;
        ws.send(input.value);
        input.value = "";
      }
    </script>
  </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A client left the chat")
