from typing import Dict, Any, List
import random
import string
import requests
import socket
import asyncio
import logging
import os
import struct
from pathlib import Path
import bencodepy
from torrent_file import TorrentFile
from peer_message import Handshake, Request
from peer import TorrentPeer
from piece_manager import PieceManager
timout = 5
logging.basicConfig(level=logging.DEBUG)
class TorrentLeecher(TorrentPeer):
    def __init__(self, torrent_filepath: str, output_path: str = None, 
                 port: int = 12345, peer_id: int = None): 
        super().__init__(port, peer_id)
        self.torrent = TorrentFile(torrent_filepath)
        self.output_path = output_path \
                            if output_path is not None \
                            else Path(torrent_filepath).with_suffix('') 
        logging.debug(self.torrent.number_of_pieces)
        self.piece_manager = PieceManager(self.torrent, output_path)

    def get_peers(self) -> Dict[str, Any]:
        response = self._send_request_to_tracker()
        return response.json()["peers"]

    async def download_from_peer(self, peer: Dict[str, str]):
        """
        Args:
            peer (Dict[str, Any]): 
                {
                    "peer_id": 1234,
                    "ip": 126.0.0.1,
                    "port": 25
                }
        """
        try:
            # Open connection
            reader, writer = await asyncio.wait_for(asyncio.open_connection(peer["ip"], int(peer["port"])), timeout=5) 
            # Create handshake msg
            handshake_msg = Handshake(
                self.torrent.info_hash.encode(), 
                self.peer_id.encode()
            ).encode()
            # Send handshake msg
            writer.write(handshake_msg)
            await writer.drain()
            # Wait for Handshake response from peer
            response = await reader.read(68)
            if not Handshake.is_valid(response):
                raise Exception("Invalid handshake response")
            print("Receive handshake response")
            # Start requesting
            while not self.piece_manager.completed:
                request_msg = self.piece_manager.get_request_msg()
                # Send request
                writer.write(request_msg)
                await writer.drain()
                # Response length
                msg = await reader.read(4)
                # ### Check if fail -> mark pending_pieces

                response_len = struct.unpack('>I', msg[:4])[0]
                logging.debug(f"Piece response len: {response_len}")
                # Piece 
                piece = await reader.read(response_len)
                logging.debug(f"Received piece length {len(piece)}")
                self.piece_manager.receive_piece(piece, response_len)
            
            print("Download successfully!")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print("Error caught: ", e)
            raise e
    
    async def download(self) -> None:
        try:
            peers = self.get_peers()
            logging.debug(peers)
            tasks = [self.download_from_peer(peer) for peer in peers]

            await asyncio.gather(*tasks)
        except Exception as e:
            self._send_request_to_tracker("stopped")



if __name__ == "__main__":
    leecher = TorrentLeecher("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/data/test/table-mountain.mp4.torrent",
                             "D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/result.mp4")
    asyncio.run(leecher.download())
        
        

    
