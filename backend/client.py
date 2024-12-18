import json
import socket
import sys
import time
from symtable import Function
from typing import Callable


MAP_BITES = 262144
PLAYER_BITES = 4096

class Client:
    def __init__(self, port: int, host: str):
        self.port = port
        self.host = host
        self.socket: socket = None
        self.socket_name: str = "NONE"
        self.address: str = "NONE"

    def setup_network(self) -> None:
        """Setup network connection to game server."""
        try:
            print(f"Attempting to connect to {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket_name = self.socket.getsockname()
            self.address = f"{self.socket_name[0]}:{self.socket_name[1]}"
            pass
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            sys.exit(1)

    def get_map(self) -> str:
        try:
            while True:
                data = json.loads(self.socket.recv(MAP_BITES).decode())
                if 'map' in data:
                    return data['map']
        except Exception as e:
            print(f"Error while recieving map: {e}")

    def receive_data(self, process_data: Callable) -> None:
        buffer = ""
        while True:
            if not hasattr(self, 'socket') or not self.socket:
                break

            try:
                chunk = self._receive_from_socket()
                if not chunk:
                    continue

                buffer += chunk

                messages = buffer.split('\n')
                buffer = messages[-1]

                for message in messages[:-1]:
                    try:
                        process_data(message)
                    except json.JSONDecodeError:
                        continue

            except Exception as e:
                self._handle_receive_exception(e)
                if not hasattr(self, 'socket') or not self.socket:
                    break

    def send_data(self, data : {}) -> None:
        try:
            serialized_info = json.dumps(data)
            self._send_to_client(serialized_info)
        except Exception as e:
            self._handle_send_exception(e)

    def _send_to_client(self, data : {}) -> None:
        """Sends the serialized player info to the client."""
        if self.socket:
            self.socket.sendall((data + '\n').encode())

    def _handle_send_exception(self, exception : Exception) -> None:
        """Handles exceptions during the send process."""
        print(f"Error sending player information: {exception}")

    def _receive_from_socket(self) -> None:
        """Receives and decodes data from the client socket."""
        try:
            return self.socket.recv(PLAYER_BITES).decode()
        except:
            return ""

    def _handle_receive_exception(self, exception):
        """Handles exceptions that occur during data reception."""
        if isinstance(exception, (ConnectionResetError, ConnectionAbortedError)):
            print("Lost connection to server. Attempting to reconnect...")
            self._attempt_reconnect()
        else:
            print(f"Error receiving data: {exception}")

    def _attempt_reconnect(self):
        """Attempt to reconnect to the server."""
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                print("Successfully reconnected to server")
                return True
            except:
                attempt += 1
                time.sleep(1)
        print("Failed to reconnect to server")
        sys.exit()
