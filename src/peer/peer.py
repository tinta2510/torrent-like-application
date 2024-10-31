"""Module provide a Class for Torrent Peer"""
from typing import Dict, Union
import random
import string
import requests
import bencodepy
from torrent_file import TorrentFile

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
        self.peer_id = self._generate_peer_id()
        self.port = port

    def _generate_peer_id(self):
        # Define client ID and version (e.g., "PY" for Python client version 1.0)
        client_id = '-PY1000-'
        # Generate a random alphanumeric string of length 12
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        # Combine to form the peer_id
        peer_id = client_id + random_part
        return peer_id

    def _send_request_to_tracker(self, torrent_filepath: str, params: Dict[str, Union[str, int]]) -> bytes:
        with open(torrent_filepath, "rb") as torrent_file:
            torrent_data = bencodepy.decode(torrent_file.read())
        tracker_url = torrent_data[b"announce"].decode('utf-8')  
        try:
            response = requests.get(tracker_url + "/announce", params=params, timeout=10)
            response.raise_for_status()  # Raise error if status is not 200
            print("Tracker Response:", response.content)
            return response.content
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
            "uploaded": 0,
            "downloaded": 0,
            "left": 0,
            "compact": 1,
            "event": "started"
        }
        response_content = self._send_request_to_tracker(torrent_filepath, params)

        return output_path

    def get_peers(self, torrent_filepath: str):
        params = {
            "info_hash": TorrentFile.get_info_hash(torrent_filepath),
            "peer_id": self.peer_id,
            "port": self.port,
            "uploaded": 0,
            "downloaded": 0,
            "left": 0,
            "compact": 1,
            "event": "started"
        }
        response_content = self._send_request_to_tracker(torrent_filepath, params)
        return response_content

if __name__=="__main__":
    client = TorrentPeer()
    client.seed("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/docs", [["http://192.168.1.7:8080"]])
# End-of-file (EOF)
