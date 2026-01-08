import asyncio
import json
import websockets
import random
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class WebSocketWorker(QObject):
    data_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)
    
    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        self.running = True

    async def connect_and_listen(self):
        uri = f"ws://{self.ip_address}/ws"
        while self.running:
            try:
                self.connection_status.emit(False)
                print(f"Attempting to connect to {uri}...")
                async with websockets.connect(uri) as websocket:
                    self.connection_status.emit(True)
                    print("Connected!")
                    while self.running:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            self.data_received.emit(data)
                        except websockets.exceptions.ConnectionClosed:
                            print("Connection closed")
                            break
                        except json.JSONDecodeError:
                            print(f"Invalid JSON: {message}")
            except Exception as e:
                print(f"Connection error: {e}")
                self.connection_status.emit(False)
                await asyncio.sleep(2) # Retry delay

    def run(self):
        asyncio.run(self.connect_and_listen())

    def stop(self):
        self.running = False

class MockWorker(QObject):
    data_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)
    
    def __init__(self, ip_address=None):
        super().__init__()
        self.running = True

    async def simulate_data(self):
        self.connection_status.emit(True)
        while self.running:
            # Simulate data
            t1 = 25.0 + random.uniform(-5, 5) + (random.random() * 80 if random.random() > 0.95 else 0) # Occasional spike
            t2 = 30.0 + random.uniform(-2, 2)
            t3 = 95.0 + random.uniform(0, 10) # Near alarm
            alarm = t1 > 100 or t2 > 100 or t3 > 100
            
            data = {"t1": t1, "t2": t2, "t3": t3, "alarm": alarm}
            self.data_received.emit(data)
            await asyncio.sleep(2)

    def run(self):
        asyncio.run(self.simulate_data())

    def stop(self):
        self.running = False
