"""Module provide a Class for Torrent Peer"""
from typing import Dict, Union
import random
import string
import requests
import socket
import asyncio
import bencodepy
from torrent_file import TorrentFile
from peer_message import Handshake, Request

class TorrentPeer:
    """
    A class to represent a peer in a torrent network, providing methods to create 
    torrent files, send tracker requests, and seed files for sharing in the network.

    Attributes:
        peer_id (str): Unique identifier for the peer generated with a specific client ID.
        port (int): Port number the peer uses for communication (default is 6881).

    Methods:
        __init__(port=6881): Initializes a peer with a generated peer_id and specified port.
        
        _generate_peer_id(): Generates a unique peer_id for the peer.
        
        _create_torrent_file(input_path, trackers, piece_length=262144, output_path=None): 
            Creates a torrent file for the specified directory or file for seeding.
        
        _send_request_to_tracker(torrent_file, params_url): Sends a request to a specified 
            tracker with parameters and handles the response to retrieve peer information.
        
        _create_params_url(info_hash, peer_id, port, uploaded, downloaded, left, compact, event): 
            Creates a URL-encoded query string for tracker requests.
        
        seed(input_path, trackers, piece_length=262144, output_path=None): 
            Creates a torrent file and initiates seeding by communicating with a tracker.
        
        get_peers(torrent_file): Sends a request to the tracker's announce URL to retrieve 
            a list of peers sharing the specified torrent.
    """
    def __init__(self, port: int = 6881):
        self.peer_id:str = self._generate_peer_id()
        self.port = port

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
        response_content = self._send_request_to_tracker(torrent_filepath, params)

        return output_path

    def get_peers(self, torrent_filepath: str):
        params = {
            "info_hash": TorrentFile.get_info_hash(torrent_filepath),
            "peer_id": self.peer_id,
            "port": self.port,
            "event": "started"
        }
        response = self._send_request_to_tracker(torrent_filepath, params)
        return response.json()

    def handshake(self, socket, torrent_filepath):
        info_hash: bytes = TorrentFile.get_info_hash(torrent_filepath).encode("utf-8")
        handshake_message = Handshake(info_hash, self.peer_id.encode("utf-8")).encode()
        socket.send(handshake_message)
        response = socket.recv(68)

        if not Handshake.isValid(response):
            print("Invalid handshake response.")
            return False
        print("Handshake successful.")
        return True

    def request_piece(self, socket, index, begin, length):
        """Requests a specific piece from the peer."""
        request_message = Request(index, begin, length).encode()
        socket.send(request_message)
    

    def download_piece(self, socket, index, length=2**14):
        """Downloads a piece by sending a request and reading the response."""
        begin = 0
        while begin < length:
            self.request_piece(socket, index, begin, length)
            response = socket.recv(4 + 9 + length)
            begin += length
            print(f"Downloaded piece {index} from {begin - length} to {begin}")

    # def download(self, torrent_filepath) -> None:
    #     peers = self.get_peers(torrent_filepath)
    #     for peer in peers:
    #         sock = self.connect(peer.ip, peer.port)
    #     if (self.handshake(sock, torrent_filepath))

    async def send_peer_message(self, host: str, port: int, message: bytes) -> None:
        reader, writer = await asyncio.open_connection(host, port)

        writer.write(message)   
        await writer.drain()

        data = await reader.read(68)


    # async def download(self, torrent_file)

    async def test_download(self, torrent_filepath, host, port):
        reader, writer = await asyncio.open_connection(host, port)

        writer.write(Handshake(TorrentFile.get_info_hash(torrent_filepath).encode(), self.peer_id.encode()).encode())   
        await writer.drain()

        data = await reader.read(68)

        if not Handshake.isValid(data):
            raise ConnectionError("connect create handshake")

        data = await reader. 
        
        

if __name__=="__main__":
    client = TorrentPeer()
    # client.seed("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/docs", [["http://192.168.1.7:8080"]])
    client.test_download("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/docs.torrent")
# End-of-file (EOF)
