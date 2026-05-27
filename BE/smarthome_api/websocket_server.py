import asyncio
import json
import threading
from datetime import datetime

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed


class WebSocketBroadcastServer:
    def __init__(self, host: str, port: int, initial_data_factory=None, incoming_event_handler=None):
        self.host = host
        self.port = port
        self.initial_data_factory = initial_data_factory
        self.incoming_event_handler = incoming_event_handler
        self.clients = set()
        self.loop = None
        self.thread = None
        self.started = threading.Event()
        self.server = None
        self.stop_future = None

    async def _broadcast(self, message: str):
        stale_clients = []
        for client in list(self.clients):
            try:
                await client.send(message)
            except ConnectionClosed:
                stale_clients.append(client)
            except Exception:
                stale_clients.append(client)

        for client in stale_clients:
            self.clients.discard(client)

    async def emit_async(self, event: str, data: dict):
        payload = {
            "event": event,
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "data": data,
        }
        await self._broadcast(json.dumps(payload, ensure_ascii=False))

    async def _send_event(self, websocket, event: str, data: dict):
        payload = {
            "event": event,
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "data": data,
        }
        await websocket.send(json.dumps(payload, ensure_ascii=False))

    async def _handle_client(self, websocket):
        self.clients.add(websocket)
        try:
            if self.initial_data_factory is not None:
                event, data = self.initial_data_factory()
                await self._send_event(websocket, event, data)

            async for raw_message in websocket:
                try:
                    parsed = json.loads(raw_message)
                except json.JSONDecodeError:
                    parsed = {"message": raw_message}

                event = str(parsed.get("event") or "ws.client_message")
                data = parsed.get("data")
                if not isinstance(data, dict):
                    data = {"payload": parsed}

                if self.incoming_event_handler is not None:
                    await self.incoming_event_handler(event, data)
                else:
                    await self.emit_async(event, {**data, "clients": len(self.clients)})
        finally:
            self.clients.discard(websocket)

    async def _run_server(self):
        self.stop_future = self.loop.create_future()
        self.server = await serve(self._handle_client, self.host, self.port)
        self.started.set()
        try:
            await self.stop_future
        finally:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
            self.stop_future = None

    def _run_forever(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        server_task = self.loop.create_task(self._run_server())
        try:
            self.loop.run_forever()
        finally:
            pending_tasks = [
                task for task in asyncio.all_tasks(self.loop)
                if task is not server_task and not task.done()
            ]
            for task in pending_tasks:
                task.cancel()
            if pending_tasks:
                self.loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
            if not server_task.done():
                server_task.cancel()
                self.loop.run_until_complete(asyncio.gather(server_task, return_exceptions=True))
            self.loop.close()
            self.loop = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.started.clear()
        self.thread = threading.Thread(target=self._run_forever, daemon=True)
        self.thread.start()
        self.started.wait(timeout=3)

    def stop(self):
        if self.loop is None:
            return

        def shutdown():
            if self.stop_future is not None and not self.stop_future.done():
                self.stop_future.set_result(None)
            self.loop.stop()

        self.loop.call_soon_threadsafe(shutdown)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        self.thread = None

    def emit(self, event: str, data: dict):
        if self.loop is None:
            return
        future = asyncio.run_coroutine_threadsafe(self.emit_async(event, data), self.loop)
        try:
            future.result(timeout=1)
        except Exception:
            pass

