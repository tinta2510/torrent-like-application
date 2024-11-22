"""Module for Torrent Peer class"""
import aiofiles
import os
from typing import List, Dict, Any
import requests
import asyncio
import struct
from uuid import uuid4
import aiofiles
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm
from torrent_peer.piece_manager import PieceManager
from torrent_peer.torrent_file import TorrentFile
from torrent_peer.utils import get_unique_filename, get_local_ip
from torrent_peer.peer_message import Handshake, Piece
from torrent_peer.config_loader import TRACKER_URL, TORRENT_DIR, DOWNLOAD_DIR, INTERVAL

class TorrentPeer:
    def __init__(self, port: int = None):
        self.port = port or 0 # 0: Find any available port
        self.local_ip = get_local_ip()
        # Containts torrents to be seeded
        # {
        #     <info_hash_1>: {
        #         "filepath": "<filepath>"
        #         "torrent_filepath": "<torrent_filepath>"
        #     },
        #     <info_hash_2>: {
        #         "filepath": "<filepath>"
        #         "torrent_filepath": "<torrent_filepath>"
        #     }
        # }
        self.seeding_torrents = {}
        self.leeching_torrents: Dict[bytes, PieceManager] = {}

    def _send_request_to_tracker(self, torrent_filepath: str, event: str = None) -> requests.Response:
        torrent = TorrentFile(torrent_filepath)
        tracker_url = torrent.tracker_url
        params = {
            "info_hash": torrent.info_hash.hex(), # ???
            "port": self.port,
            # "ip": self.local_ip ??
        }
        
        if event is not None:
            params["event"] = event
        try:
            response = requests.get(tracker_url + "/announce", params=params, timeout=10)
            response.raise_for_status()  # Raise error if status is not 200
            return response
        except requests.exceptions.RequestException as e:
            return None
    ##### For seeding - BEGIN #####
    def _upload_torrent_to_tracker(self, name: str, description: str, torrent_filepath: str):
        torrent = TorrentFile(torrent_filepath)
        tracker_url = torrent.tracker_url
        with open(torrent_filepath, "rb") as file:
            files = {'file': file}
            data = {
                "name": name,
                "description": description,
            }
            params = {
                "info_hash": torrent.info_hash.hex(),
                "port": self.port,
                # "ip": self.local_ip ???
                "event": "started"
            }
            try:
                response = requests.post(tracker_url + "/announce", files=files, data=data, params=params, timeout=10)
                response.raise_for_status()
                return response   
            except requests.exceptions.RequestException as e:
                tqdm.write(f"Error connecting to tracker.\nError: {e}")
                return None

    def seed(self, input_path: str, 
                   trackers: List[List[str]], 
                   public: bool = True,
                   piece_length: int = None, 
                   torrent_filepath: str = None,
                   **kwargs):
        try:
            if not os.path.exists(input_path): 
                raise FileNotFoundError(input_path, "does not exists.")
            
            if not piece_length: piece_length = 2**14
            elif piece_length > 2**14: piece_length = 2**14

            torrent_filepath = TorrentFile.create_torrent_file(
                input_path=input_path,
                trackers=trackers,
                output_path=torrent_filepath or os.path.join(TORRENT_DIR, os.path.basename(input_path) + ".torrent"),
                piece_length=piece_length
            )
            torrent = TorrentFile(torrent_filepath)

            # Add to list of active torrents
            self.seeding_torrents[torrent.info_hash] = {
                "torrent_filepath": torrent.filepath,
                "filepath": input_path
            }
            # Upload file to tracker or not
            if public:
                name = kwargs.get("name", None) or torrent.filename
                description = kwargs.get("description", "")
                self._upload_torrent_to_tracker(name, description, torrent.filepath)
            else:
                self._send_request_to_tracker(torrent.filepath, "started")
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
        except Exception as e:
            raise Exception("Exception appeared when seeding: ", e) from e

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        try: 
            request = await reader.read(68)
            if not request:
                raise Exception(f"Connection to client {addr} closed!") 

            if not Handshake.is_valid(request):
                raise Exception("Invalid handshake response")

            # Get correct torrent to seed
            handshake_request = Handshake.decode(request)
            info_hash = handshake_request.info_hash
            if info_hash not in self.seeding_torrents:
                raise Exception("Requested torrent is not found.")
            
            curr_torrent_metadata = self.seeding_torrents[info_hash]
            curr_torrent = TorrentFile(curr_torrent_metadata["torrent_filepath"])
            # Send handshake msg
            handshake_msg = Handshake(info_hash).encode()
            writer.write(handshake_msg)
            await writer.drain()

            # Listening for request after handshaking
            while True:
                msg = await reader.read(4)
                if not msg:
                    break  

                request_length = struct.unpack('>I', msg)[0]
                msg = await reader.read(request_length)
                (id, index, begin, length) = struct.unpack('>bIII', msg)
                
                piece = await self.get_piece_for_seeding(curr_torrent, curr_torrent_metadata, index, length)
                piece_msg = Piece(index, begin, piece).encode()
                tqdm.write(f"Send PIECE with index {index} to peer {addr}")
                writer.write(piece_msg)
                await writer.drain()    

            writer.close()
            await writer.wait_closed()            
        except Exception as e:
            tqdm.write(f"Error caught in handle_client {addr}: {e}")
        finally:
            tqdm.write(f"Closed connection to {addr}")
                

    async def get_piece_for_seeding(self, 
                              curr_torrent: TorrentFile, 
                              curr_torrent_metadata: Dict[str, Any], 
                              index: int, 
                              length: int):
        piece_length = curr_torrent.piece_length
        filepath = curr_torrent_metadata["filepath"]

        if curr_torrent.files == None: # Single file case
            async with aiofiles.open(filepath, "rb") as file:
                await file.seek(index * piece_length)
                piece = await file.read(length)
        else: 
            lower_offset = index * piece_length
            piece = b""
            reading_length = length
            for (path, file_length) in curr_torrent.files:
                if lower_offset < file_length:
                    async with aiofiles.open(os.path.join(filepath, path), "rb") as file:
                        await file.seek(lower_offset)
                        piece += await file.read(reading_length)
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
    def get_torrents():
        try:
            response = requests.get(TRACKER_URL + "/torrents")
            response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
            torrents = response.json()
            return torrents
        except requests.HTTPError as e:
            # Handle HTTP errors (e.g., 404, 500, etc.)
            raise RuntimeError(f"HTTP error occurred: {e}") from e
        except requests.RequestException as e:
            # Handle other requests-related issues (e.g., connection errors)
            raise RuntimeError(f"Request error occurred: {e}") from e
        except ValueError:
            # Handle JSON decoding error (e.g., if response is not in JSON format)
            raise RuntimeError("Invalid JSON in response") from e
        except Exception as e:
            raise Exception("Error occured during getting torrents from tracker") from e

    @staticmethod
    async def get_torrent_by_info_hash(info_hash: bytes):
        try:
            response = requests.get(TRACKER_URL + f"/torrents/{info_hash}")
            response.raise_for_status()
            
            torrent_filepath = os.path.join(DOWNLOAD_DIR, str(uuid4()))

            async with aiofiles.open(torrent_filepath, "wb") as f:
                await f.write(response.content)

            filename = TorrentFile(torrent_filepath).filename + ".torrent"

            dir = os.path.dirname(torrent_filepath)
            new_torrent_filepath = get_unique_filename(os.path.join(dir, filename))
            os.rename(torrent_filepath, new_torrent_filepath)    

            return new_torrent_filepath
        except requests.HTTPError as e:
            # Handle HTTP errors (e.g., 404, 500, etc.)
            raise RuntimeError(f"HTTP error occurred: {e}") from  e
        except requests.RequestException as e:
            # Handle other requests-related issues (e.g., connection errors)
            raise RuntimeError(f"Request error occurred: {e}") from e
        except FileNotFoundError:
            raise FileNotFoundError(f"The file does not exist: {e}") from e
        except PermissionError:
            raise PermissionError(f"Permission denied. You may not have the right permissions. {e}") from e
        except Exception as e:
            raise Exception(f"Error occured during getting torrent by info_hash from tracker. {e}") from e

    async def download_from_peer(self, 
                                 piece_manager: PieceManager, 
                                 torrent: TorrentFile, 
                                 peer: Dict[str, str],
                                 pbar: tqdm_asyncio):
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
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(peer["ip"], int(peer["port"])), 
                timeout=5
            ) 
            tqdm.write(f"Connected to ({peer['ip']}, {peer['port']})")

            piece_manager.active_peers.append(peer)
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
                # Piece 
                piece = await reader.read(response_len)
                idx = await piece_manager.receive_piece(piece)

                tqdm.write(f"Received piece with index {idx} from {peer}\n")
                pbar.update(1)
                pbar.refresh()
            
            tqdm.write("Download successfully!")

            writer.close()
            await writer.wait_closed()
        except asyncio.TimeoutError:
            tqdm.write(f"Connection to {peer} attempt timed out.")
        except ConnectionRefusedError:
            tqdm.write(f"Connection to {peer} was refused by the peer.")
        except asyncio.IncompleteReadError:
            tqdm.write(f"Failed to read data from the peer {peer}.")
        except Exception as e:
            tqdm.write(f"An unexpected error occurred at download_from_peer: {e}")
        finally:
            if peer in piece_manager.active_peers:
                piece_manager.active_peers.remove(peer)
            

    async def download(self, torrent_filepath: str, pbar_position: int, output_dir: str = None):
        output_dir = output_dir or DOWNLOAD_DIR
        torrent = TorrentFile(torrent_filepath)
        tqdm.write(f"Start downloading {torrent.info_hash}")

        piece_manager = PieceManager(torrent, output_dir)
        total_pieces = len(piece_manager.pieces_status)
        with tqdm_asyncio(total=total_pieces, 
                          desc=f"Downloading {os.path.basename(piece_manager.output_name)}", 
                          position=pbar_position, 
                          leave=False,
                          unit="piece") as pbar:
            try:
                while not piece_manager.completed:
                    peers = self.get_peers(torrent_filepath)
                    for peer in peers:
                        if peer not in piece_manager.active_peers:
                            asyncio.create_task(self.download_from_peer(piece_manager, torrent, peer, pbar))
                    await asyncio.sleep(INTERVAL)
            except Exception as e:
                tqdm.write(f"Exception occured at download function: {e}")

    async def start_seeding(self):
        try:
            """
            Main coroutine to start the server.
            """
            server = await asyncio.start_server(self.handle_client, "127.0.0.1", self.port)
            addr = server.sockets[0].getsockname()

            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            tqdm.write("Program terminated using Ctr+C")
        except Exception as e:
            tqdm.write(f"Exception appeared when start server: {e}")
        finally:
            for value in self.seeding_torrents.values():
                self._send_request_to_tracker(value["torrent_filepath"], "stopped")
    ##### For downloading - BEGIN #####



      
        
