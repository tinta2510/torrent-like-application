"""Module provide a common class for Torrent Peer (both seeder and uploader)"""
from typing import Dict, Union
import random
import string
import requests
from pathlib import Path
import socket
import logging
import asyncio
import bencodepy
from torrent_file import TorrentFile
from peer_message import Handshake, Request
logging.basicConfig(level=logging.DEBUG)
class TorrentPeer:
    def __init__(self, port: int = 12345, peer_id: int = None):
        self.peer_id:str = peer_id if peer_id is not None else self._generate_peer_id()
        self.port = port
        self.torrent: TorrentFile = None

    def _generate_peer_id(self) -> str:
        # Define client ID and version (e.g., "PY" for Python client version 1.0)
        client_id = '-PY1000-'
        # Generate a random alphanumeric string of length 12
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        # Combine to form the peer_id
        peer_id = client_id + random_part
        return peer_id
    
    def _send_request_to_tracker(self, event: str = None) -> requests.Response:
        tracker_url = self.torrent.tracker_url

        params = {
            "info_hash": self.torrent.info_hash,
            "peer_id": self.peer_id,
            "port": self.port,
        }
        if event is not None:
            params["event"] = event
        try:
            response = requests.get(tracker_url + "/announce", params=params, timeout=10)
            response.raise_for_status()  # Raise error if status is not 200
            print("Tracker Response:", response.json())
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to tracker.\nError: {e}")
            return None
    
