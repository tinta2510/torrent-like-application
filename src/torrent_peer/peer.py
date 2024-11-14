"""Module for Torrent Peer class"""
import configparser
import os
from typing import List, Dict, Any
import requests
import asyncio
import logging
import struct
import traceback
from pathlib import Path
from torrent_peer.piece_manager import PieceManager
from torrent_peer.torrent_file import TorrentFile
from torrent_peer.utils import get_unique_filename, get_local_ip
from torrent_peer.peer_message import Handshake, Piece

logging.basicConfig(level=logging.DEBUG)

# READ data from configuration file 
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
TRACKER_URL = config["peer"]["TRACKER_URL"]
TORRENT_DIR = os.path.join(CURRENT_DIR, config["peer"]["TORRENT_DIR"])
DOWNLOAD_DIR = os.path.join(CURRENT_DIR, config["peer"]["DOWNLOAD_DIR"])

class TorrentPeer:
    def __init__(self, port: int = None):
        self.port = port or 0 # 0: Find any available port
        # self.local_ip = get_local_ip() ???
        self.active_torrents = {}

    def _send_request_to_tracker(self, torrent_filepath: str, event: str = None) -> requests.Response:
        torrent = TorrentFile(torrent_filepath)

        params = {
            "info_hash": torrent.info_hash.hex(), # ???
            "port": self.port,
            # "ip": self.local_ip ??
        }
        
        if event is not None:
            params["event"] = event
        try:
            response = requests.get(TRACKER_URL + "/announce", params=params, timeout=10)
            response.raise_for_status()  # Raise error if status is not 200
            print("Tracker Response:", response.json())
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to tracker.\nError: {e}")
            return None
    ##### For seeding - BEGIN #####
    def _upload_torrent_to_tracker(self, name: str, description: str, torrent_filepath: str):
        torrent = TorrentFile(torrent_filepath)
        with open(torrent_filepath, "rb") as file:
            files = {'file': file}
            data = {
                "name": name,
                "description": description,
            }
            params = {
                "info_hash": torrent.info_hash.hex(), # ???
                "port": self.port,
                # "ip": self.local_ip ???
                "event": "started"
            }
            try:
                response = requests.post(TRACKER_URL + "/announce", files=files, data=data, params=params)
                response.raise_for_status()
                print("Tracker response: ")
                return response   
            except requests.exceptions.RequestException as e:
                print(f"Error connecting to tracker.\nError: {e}")
                return None

    def seed(self, input_path: str, 
                   trackers: List[List[str]], 
                   piece_length: int = 2**14, 
                   torrent_filepath: str = None):
        try:
            if not os.path.exists(input_path): 
                raise FileNotFoundError(input_path, "does not exists.")

            torrent_filepath = TorrentFile.create_torrent_file(
                input_path=input_path,
                trackers=trackers,
                output_path=torrent_filepath or os.path.join(TORRENT_DIR, os.path.basename(input_path) + ".torrent"),
                piece_length=piece_length
            )
            torrent = TorrentFile(torrent_filepath)

            # Add to list of active torrents
            self.active_torrents[torrent.info_hash] = {
                "torrent_filepath": torrent.filepath,
                "filepath": input_path
            }
            # Upload file to tracker or not
            while True:
                flag = input("Upload torrent file to tracker (y/n): ")
                if flag == "y": 
                    name = input("Name (.torrent): ")
                    description = input("Description: ")
                    self._upload_torrent_to_tracker(name, description, torrent.filepath)
                    break
                elif flag == "n":
                    self._send_request_to_tracker("started")
                    break
                else:
                    print("Enter 'y' or 'n' only.") 
        except Exception as e:
            print("Exception appeared when seeding: ", e)
            traceback.print_exc()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")
        try: 
            request = await reader.read(68)
            if not request:
                print(f'{addr} closed the connection')
                raise Exception(f"Connection to client {addr} closed!") 

            if not Handshake.is_valid(request):
                raise Exception("Invalid handshake response")
            print(f"Receive handshake msg from {addr}")

            # Get correct torrent to seed
            handshake_request = Handshake.decode(request)
            info_hash = handshake_request.info_hash
            if info_hash not in self.active_torrents:
                raise Exception("Requested torrent is not found.")
            
            curr_torrent_metadata = self.active_torrents[info_hash]
            curr_torrent = TorrentFile(curr_torrent_metadata["torrent_filepath"])
            # Send handshake msg
            handshake_msg = Handshake(info_hash).encode()
            writer.write(handshake_msg)
            await writer.drain()
            logging.debug(f"Sent handshake response to {addr}")

            # Listening for request after handshaking
            while True:
                msg = await reader.read(4)
                if not msg:
                    print(f'{addr} closed the connection')
                    break  

                request_length = struct.unpack('>I', msg)[0]
                msg = await reader.read(request_length)
                (id, index, begin, length) = struct.unpack('>bIII', msg)
                
                piece = self.get_piece_for_seeding(curr_torrent, curr_torrent_metadata, index, length)
                    
                piece_msg = Piece(index, begin, piece).encode()
                writer.write(piece_msg)
                await writer.drain()                
        except Exception as e:
            print(f"Error caught in handle_client {addr}: ", e)
            traceback.print_exc()
        finally:
            print(f"Closed connection to {addr}")
            writer.close()
            await writer.wait_closed()

    def get_piece_for_seeding(self, 
                              curr_torrent: TorrentFile, 
                              curr_torrent_metadata: Dict[str, Any], 
                              index: int, 
                              length: int):
        piece_length = curr_torrent.piece_length
        filepath = curr_torrent_metadata["filepath"]

        if curr_torrent.files == None: # Single file case
            with open(filepath, "rb") as file:
                file.seek(index * piece_length)
                piece = file.read(length)
        else: 
            lower_offset = index * piece_length
            piece = b""
            reading_length = length
            for (path, file_length) in curr_torrent.files:
                if lower_offset < file_length:
                    with open(os.path.join(filepath, path), "rb") as file:
                        file.seek(lower_offset)
                        piece += file.read(reading_length)
                    if len(piece) == length:
                        break
                    reading_length = length - len(piece)
                    lower_offset = 0
                else:
                    lower_offset -= file_length
        return piece
    ##### For seeding - END #####

    ##### For downloading - BEGIN #####
    def get_peers(self, torrent_filepath: str) -> Dict[str, Any]:
        response = self._send_request_to_tracker(torrent_filepath)
        return response.json().get("peers", {})
    
    @staticmethod
    def get_torrent():
        # GET all torrents
        response = requests.get(TRACKER_URL + "/torrents")
        torrents = response.json()
        print("Available torrents: ", torrents)
        info_hash = input("Enter info_hash: ")
        file_path = TorrentPeer.get_torrent_by_info_hash(torrents[info_hash]["name"], info_hash)
        return file_path
    
    @staticmethod
    def get_torrent_by_info_hash(file_name: str, info_hash: bytes):
        response = requests.get(TRACKER_URL + f"/torrents/{info_hash}")

        if response.status_code != 200:
            print(f"Fail to download file: ", response.status_code)
        file_path = os.path.join(DOWNLOAD_DIR, file_name)

        file_path = get_unique_filename(file_path)

        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path

    async def download_from_peer(self, piece_manager: PieceManager, torrent: TorrentFile, peer: Dict[str, str]):
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
            handshake_msg = Handshake(torrent.info_hash).encode()

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
            while not piece_manager.completed:
                request_msg = piece_manager.get_request_msg()
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
                piece_manager.receive_piece(piece)
            
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
            print(f"An unexpected error occurred at download_from_peer: {e}")
            traceback.print_exc()
        finally:
            writer.close()
            await writer.wait_closed()

    async def download(self, torrent_filepath: str, output_dir: str = None) -> None:
        output_dir = output_dir or DOWNLOAD_DIR
        torrent = TorrentFile(torrent_filepath)
        try:
            peers = self.get_peers(torrent_filepath)
            piece_manager = PieceManager(torrent, output_dir)
            logging.debug(peers)
            tasks = [self.download_from_peer(piece_manager, torrent, peer) for peer in peers]

            await asyncio.gather(*tasks)
        except Exception as e:
            print("Exception occured at download function", e)
            traceback.print_exc()

    async def start(self, stop_event):
        try:
            """
            Main coroutine to start the server.
            """
            server = await asyncio.start_server(self.handle_client, "127.0.0.1", self.port)
            addr = server.sockets[0].getsockname()
            print(f"Serving on {addr}")

            # async with server:
            #     await server.serve_forever()
                            # Run the server until the stop_event is set
            while not stop_event.is_set():
                await asyncio.sleep(0.1)  # Non-blocking wait
        except KeyboardInterrupt:
            print("Program terminated using Ctr+C")
        except Exception as e:
            print("Exception appeared when start server", e)
        finally:
            for value in self.active_torrents.values():
                self._send_request_to_tracker(value["torrent_filepath"], "stopped")
    ##### For downloading - BEGIN #####



      
        
