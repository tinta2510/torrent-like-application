from typing import Dict, Union
import random
import string
import requests
import socket
import asyncio
import bencodepy
from torrent_file import TorrentFile
from peer_message import Handshake, Request
from peer import TorrentPeer

class TorrentSeeder(TorrentPeer):
    def __init__(self, port: int = 12345, peer_id: int = None): 
        super().__init__(port, peer_id)

    def seed(self, input_path, trackers, piece_length = 262144, output_path = None):
        """
        Args:
            input_path (str): path to dir/file to be seeded
            trackers (List[List[str]]): a list of lists of trackers
            piece_length (int): length of pieces of a file/folder (default is 256KB) 
            output_path (str): path to output file
        """
        output_path = TorrentFile.create_torrent_file(input_path, trackers, piece_length,output_path)
        self.torrent = TorrentFile(output_path)
        
        response = super()._send_request_to_tracker()

        return output_path 
    
    async def upload(self):
        """
        Main coroutine to start the server.
        """
        server = await asyncio.start_server(self.handle_client, "localhost", 8888)
        addr = server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    pass