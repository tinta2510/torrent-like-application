from typing import Dict, Union, List
import random
import asyncio
import logging
import struct
from torrent_file import TorrentFile
from peer_message import Handshake, Request, Piece
from peer import TorrentPeer
logging.basicConfig(level=logging.DEBUG)
import random

class TorrentSeeder(TorrentPeer):
    def __init__(self, port: int = 12345, peer_id: int = None): 
        super().__init__(port, peer_id)
        self.input_path = None

    async def seed(self, input_path: str, trackers: List[List[str]], piece_length: int = 2**14, 
                   output_path: str = None):
        """
        Args:
            input_path (str): path to dir/file to be seeded
            trackers (List[List[str]]): a list of lists of trackers
            piece_length (int): length of pieces of a file/folder (default is 256KB) 
            output_path (str): path to output file
        """
        try:
            self.input_path = input_path
            output_path = TorrentFile.create_torrent_file(input_path, trackers, piece_length,output_path)
            self.torrent = TorrentFile(output_path)
            
            response = self._send_request_to_tracker("started")

            """
            Main coroutine to start the server.
            """
            server = await asyncio.start_server(self.handle_client, "127.0.0.1", self.port)
            addr = server.sockets[0].getsockname()
            print(f"Serving on {addr}")

            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            print("Program terminated using Ctr+C")
            self._send_request_to_tracker("stopped")
        except Exception as e:
            print("Exception appeared when seeding", e)
            self._send_request_to_tracker("stopped")
        except BaseException as e:
            print("Exception appeared when seeding", e)
            self._send_request_to_tracker("stopped")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")
        try: 
            request = await reader.read(68)
            if not request:
                    print(f'{addr} closed the connection')
                    raise Exception(f"Connection to client {addr} closed!")  # or handle the lack of message appropriately

            if not Handshake.is_valid(request):
                raise Exception("Invalid handshake response")
            print(f"Receive handshake msg from {addr}")

            handshake_msg = Handshake(
                self.torrent.info_hash.encode(), 
                self.peer_id.encode()
            ).encode()
            # Send handshake msg
            writer.write(handshake_msg)
            await writer.drain()
            logging.debug(f"Sent handshake response to {addr}")

            # Listening for request after handshaking
            while True:
                msg = await reader.read(4)
                if not msg:
                    print(f'{addr} closed the connection')
                    break  # or handle the lack of message appropriately
                request_length = struct.unpack('>I', msg)[0]

                msg = await reader.read(request_length)
    
                (id, index, begin, length) = struct.unpack('>bIII', msg)
                with open(self.input_path, "rb") as file:
                    file.seek(index * self.torrent.piece_length)
                    piece = file.read(length)
                piece_msg = Piece(index, begin, piece).encode()
                writer.write(piece_msg)
                await writer.drain()                
        except BaseException as e:
            print(f"Error caught in handle_client {addr}")
        finally:
            print(f"Closed connection to {addr}")
            writer.close()
            await writer.wait_closed()



if __name__ == "__main__":
    client = TorrentSeeder(random.randint(10000, 20000))
    asyncio.run(client.seed("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/data/test/table-mountain.mp4",
                [["http://127.0.0.1:8080"]]))