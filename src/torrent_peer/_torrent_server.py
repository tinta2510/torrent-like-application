from typing import Dict, Union
import random
import string
import requests
import struct 
import socket
import asyncio
import bencodepy
from torrent_file import TorrentFile
from peer_message import Handshake, Request, KeepAlive
class TorrentServer :
    def __init__(self, port: int = 6881):
        self.peer_id:str = self._generate_peer_id()
        self.port = port
        self.sock = None

    def _generate_peer_id(self) -> str:
        # Define client ID and version (e.g., "PY" for Python client version 1.0)
        client_id = '-PY1000-'
        # Generate a random alphanumeric string of length 12
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        # Combine to form the peer_id
        peer_id = client_id + random_part
        return peer_id

    def _send_request_to_tracker(self, torrent_filepath: str, params: Dict[str, Union[str, int]]) -> requests.Response:
        with open(torrent_filepath, "rb") as torrent_file:
            torrent_data = bencodepy.decode(torrent_file.read())
        tracker_url = torrent_data[b"announce"].decode('utf-8')  
        try:
            response = requests.get(tracker_url + "/announce", params=params, timeout=10)
            response.raise_for_status()  # Raise error if status is not 200
            print("Tracker Response:", response)
            return response
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Error connecting to tracker: {e}. Status code: {response.status_code}") from e

    def seed(self, input_path, trackers, piece_length = 262144, output_path = None):
        """
        Args:
            input_path (str): path to dir/file to be seeded
            trackers (List[List[str]]): a list of lists of trackers
            piece_length (int): length of pieces of a file/folder (default is 256KB) 
            output_path (str): path to output file
        """
        torrent_filepath = TorrentFile.create_torrent_file(input_path, trackers, piece_length,output_path)

        params = {
            "info_hash": TorrentFile.get_info_hash(torrent_filepath),
            "peer_id": self.peer_id,
            "port": self.port,
            "event": "started"
        }
        response = self._send_request_to_tracker(torrent_filepath, params)

    async def handle_handshake(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connected by {addr}")

        message: bytes = await reader.read(68)
        if not Handshake.is_valid(message):
            raise Exception("Invalid handsake")
        handshake = Handshake.decode(message)

        # Compare info_hash ... + verify handshake

        handshake = Handshake(info_hash, self.peer_id.encode())
        writer.write(handshake)


    async def handle_handshaked_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connected by {addr}")

        try: 
            while True:
                raw_length = await reader.read(4)

                if not raw_length:
                    raise Exception(e)
                
                msg_length = struct.unpack(">I", raw_length)[0]
                if msg_length == 0: # Keep alive messaage
                    pass 

                else:
                
                    msg_id = struct.unpack(">B", reader.read(1))[0]

                    if msg_id ==  
        except asyncio.CancelledError as e:
            print(f"Connection canceled for {addr}") 
        except Exception as e:
            print(e)
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"Disconnected from {addr}")

    async def main(self):
        """
        Main coroutine to start the server.
        """
        server = await asyncio.start_server(self.handle_client, "localhost", 8888)
        addr = server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    server = TorrentServer(12345)
    server.test()