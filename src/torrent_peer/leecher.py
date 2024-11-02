from typing import Dict, Any, List
import random
import string
import requests
import socket
import asyncio
import logging
import os
from pathlib import Path
import bencodepy
from torrent_file import TorrentFile
from peer_message import Handshake, Request
from peer import TorrentPeer

timout = 5

class TorrentLeecher(TorrentPeer):
    def __init__(self, torrent_filepath: str, output_path: str = None, 
                 port: int = 12345, peer_id: int = None): 
        super().__init__(port, peer_id)
        super().torrent = TorrentFile(torrent_filepath)
        self.output_path = output_path \
                            if output_path is not None \
                            else Path(torrent_filepath).with_suffix('') 

    def get_peers(self) -> Dict[str, Any]:
        response = self._send_request_to_tracker()
        return response.json()["peers"]

    async def download_from_peer(self, ip, port):
        try:
            # Open connection
            reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=5) # asyncio.wait_for
            # Create handshake msg
            handshake_msg = Handshake(
                self.torrent.info_hash.encode(), 
                self.peer_id.encode()
            ).encode()
            # Send handshake msg
            writer.write(handshake_msg)
            await writer.drain()
            # Wait for Bitfield response from peer
            response = await reader.read(68)
            # if not Handshake.is_valid(response):
            #     raise Exception("Invalid handshake response")

            pass    
        except Exception as e:
            print("Error caught: ", e)
    
    async def download(self) -> None:
        peers = self.get_peers()

        tasks = [self.download_from_peer(peer["ip"], peer["port"]) for peer in peers]

        await asyncio.gather(*tasks)




if __name__ == "__main__":
    pass
        
        

    
