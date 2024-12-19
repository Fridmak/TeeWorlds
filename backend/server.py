import socket
import threading
import json
import logging
import os, sys
import time

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class GameServer:
    """
    Game server implementation that handles multiple client connections and game state.
    """

    def __init__(self):
        """
        Initialize the game server.
        """
        self.host = settings.HOST_SERVER
        self.port = settings.PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: [socket.socket] = []
        self.players: {(str, int), dict} = {}
        self.map = None  # Изначально карта None
        self.was_working = False
        self.shutdown_event = threading.Event()

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        logging.info(f'Server started on {self.host}:{self.port}')

    def _on_client_disconnected(self, conn: socket.socket, addr: (str, int)) -> None:
        """
        Clean up when a client disconnects.
        """
        try:
            conn.close()
        except:
            pass

        if conn in self.clients:
            self.clients.remove(conn)

        player_key = f"{addr[0]}:{addr[1]}"
        if player_key in self.players:
            self.players.pop(player_key)
            logging.info(f'Player {player_key} removed from game')

        logging.info(f'Connection with {addr} closed')

        self._send_data_to_clients()

        if not self.clients and self.was_working:
            logging.info('No clients remaining, shutting down server')
            self._clean()

    def _send_data_to_clients(self) -> None:
        """Broadcast current player data to all connected clients."""
        try:
            # Отправляем только данные игроков
            player_data = json.dumps(self.players).encode('utf-8') + b'\n'
            for client in self.clients:
                client.sendall(player_data)
        except Exception as e:
            logging.error(f'Error sending data to players: {str(e)}')

    def _broadcast_map(self) -> None:
        """Broadcast map data to all connected clients."""
        try:
            map_data = json.dumps({'map': self.map}).encode('utf-8') + b'\n'
            for client in self.clients:
                client.sendall(map_data)
        except Exception as e:
            logging.error(f'Error broadcasting map: {str(e)}')

    def handle_client(self, conn: socket.socket, addr: (str, int)) -> None:
        """
        Handle individual client connection.
        """
        player_key = f"{addr[0]}:{addr[1]}"
        buffer = ""

        try:
            while not self.shutdown_event.is_set():  # Check if server is shutting down
                chunk = conn.recv(262144).decode('utf-8')
                if not chunk:
                    break

                self.was_working = True
                buffer += chunk

                messages = buffer.split('\n')
                buffer = messages[-1]

                for message in messages[:-1]:
                    try:
                        loaded_data = json.loads(message)

                        if 'map' in loaded_data:
                            # Сохраняем карту только если в ней есть изменения
                            if loaded_data['map'] != self.map:
                                logging.info(f'Map changed, old: {self.map is None}, new: {loaded_data["map"] is None}')  # DEBUG
                                self.map = loaded_data['map']
                                logging.info(f'Received map from {player_key}')
                                self._broadcast_map()
                            continue

                        if 'disconnect' in loaded_data:
                            if len(self.players) <= 1:
                                self._clean()
                            player_id = loaded_data['id']

                            for key, player in list(self.players.items()):
                                if player.get('id') == player_id:
                                    self.players.pop(key)
                                    logging.info(f'Player {player_id} disconnected')

                                    if key == player_key:
                                        return
                            self._send_data_to_clients()
                            continue

                        self.players[player_key] = loaded_data
                        self._send_data_to_clients()
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logging.error(f'Error processing data from {player_key}: {str(e)}')
                        buffer = ""
        except Exception as e:
            pass
        finally:
            self._on_client_disconnected(conn, addr)

    def start(self):
        """Start the game server and handle incoming connections."""
        try:
            while not self.shutdown_event.is_set():
                try:
                    conn, addr = self.server_socket.accept()
                    logging.info(f'Connected by {addr}')

                    if self.map:
                        logging.info(f'Sending existing map to new client')
                        map_data = json.dumps({'map': self.map}).encode('utf-8') + b'\n'
                        conn.sendall(map_data)
                    else:
                        logging.info(f'Sending empty map to new client')
                        map_data = json.dumps({'map': None}).encode('utf-8') + b'\n'
                        conn.sendall(map_data)

                    time.sleep(0.1)

                    self.clients.append(conn)

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error as e:
                    if not self.shutdown_event.is_set():
                        logging.error(f"Socket error: {e}")

        except KeyboardInterrupt:
            logging.info("Server shutting down...")
            self._send_shutdown_notification()
            self._clean()

    def _send_shutdown_notification(self):
        """Notify all clients before shutting down."""
        try:
            shutdown_msg = json.dumps({"server_shutdown": True}).encode('utf-8')
            for client in self.clients:
                client.sendall(shutdown_msg)
        except:
            pass

    def _clean(self):
        """Clean up server resources."""
        self._send_shutdown_notification()
        self.shutdown_event.set()
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.server_socket.close()
        logging.info('Server closed')
        sys.exit()


if __name__ == "__main__":
    server = GameServer()
    server.start()
