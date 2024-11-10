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
import configparser
from torrent_file import TorrentFile
from peer_message import Handshake, Request
from peer import TorrentPeer
from piece_manager import PieceManager

logging.basicConfig(level=logging.DEBUG)

# Configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(config_path)
TRACKER_URL = config["peer"]["TRACKER_URL"]
TORRENT_DIR = os.path.join(CURRENT_DIR, config["peer"]["TORRENT_DIR"])

class TorrentLeecher(TorrentPeer):
    def __init__(self, torrent_filepath: str, output_path: str = None, 
                 port: int = 12345, peer_id: int = None): 
        super().__init__(port, peer_id)
        self.torrent = TorrentFile(torrent_filepath)
        self.output_path =  output_path or Path(torrent_filepath).with_suffix('')
        self.piece_manager = PieceManager(self.torrent, self.output_path)

    def get_peers(self) -> Dict[str, Any]:
        response = self._send_request_to_tracker()
        return response.json().get("peers", {})
    
    @staticmethod
    def get_torrent():
        # GET all torrents
        response = requests.get(TRACKER_URL + "/torrents")
        torrents = response.json()
        print("Available torrents: ", torrents)
        info_hash = input("Enter info_hash: ")
        file_path = TorrentLeecher.get_torrent_by_info_hash(torrents[info_hash]["name"], info_hash)
        return file_path
    
    @staticmethod
    def get_torrent_by_info_hash(file_name: str, info_hash: str):
        response = requests.get(TRACKER_URL + f"/torrents/{info_hash}")

        if response.status_code != 200:
            print(f"Fail to download file: ", response.status_code)
        file_path = os.path.join(TORRENT_DIR, file_name)

        # Check for filename collision and adjust filename if needed
        if os.path.exists(file_path):
            base, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(file_path):
                new_filename = f"{base}_{counter}{ext}"
                file_path = os.path.join(TORRENT_DIR, new_filename)
                counter += 1

        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path

    async def download_from_peer(self, peer: Dict[str, str]):
        """
        Args:
            peer (Dict[str, Any]): 
                {
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
            if not response:
                raise Exception(f"Connection to {peer} closed.")
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
                if not msg:
                    raise Exception(f"Connection to {peer} closed.")
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
        except asyncio.TimeoutError:
            print(f"Connection to {peer} attempt timed out.")
        except ConnectionRefusedError:
            print(f"Connection to {peer} was refused by the peer.")
        except asyncio.IncompleteReadError:
            print(f"Failed to read data from the peer {peer}.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        except Exception as e:
            print("Error caught: ", e)
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def download(self) -> None:
        try:
            peers = self.get_peers()
            logging.debug(peers)
            tasks = [self.download_from_peer(peer) for peer in peers]

            await asyncio.gather(*tasks)
        except Exception as e:
            self._send_request_to_tracker("stopped")

if __name__ == "__main__":
    torrent_filepath = TorrentLeecher.get_torrent()
    leecher = TorrentLeecher(torrent_filepath)
    asyncio.run(leecher.download())
        

    
