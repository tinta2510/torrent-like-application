from typing import Dict, Union
import random
import string
import requests
import socket
import asyncio
import logging
import struct
import bencodepy
from torrent_file import TorrentFile
from peer_message import Handshake, Request, Piece
from peer import TorrentPeer
logging.basicConfig(level=logging.DEBUG)
import random
class TorrentSeeder(TorrentPeer):
    def __init__(self, port: int = 12345, peer_id: int = None): 
        super().__init__(port, peer_id)
        self.input_path = None

    async def seed(self, input_path, trackers, piece_length = 2**14, output_path = None):
        
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
        except Exception as e:
            print("Caught", e)
            self._send_request_to_tracker("stopped")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")
        try: 
            request = await reader.read(68)
            if not Handshake.is_valid(request):
                raise Exception("Invalid handshake response")
            print("Receive handshake msg")

            handshake_msg = Handshake(
                self.torrent.info_hash.encode(), 
                self.peer_id.encode()
            ).encode()
            # Send handshake msg
            writer.write(handshake_msg)
            await writer.drain()
            logging.debug(f"Sent handshake response to {addr}")
            while True:
                msg = await reader.read(4)
                logging.debug(f"Msg received:{msg}")
                request_length = struct.unpack('>I', msg)[0]
                logging.debug(request_length)

                msg = await reader.read(request_length)
                logging.debug(f"Msg received:{msg}")
    
                (id, index, begin, length) = struct.unpack('>bIII', msg)
                with open(self.input_path, "rb") as file:
                    file.seek(index * self.torrent.piece_length)
                    piece = file.read(length)
                piece_msg = Piece(index, begin, piece).encode()
                logging.debug(f"Message len sent: {len(piece_msg)}")
                writer.write(piece_msg)
                await writer.drain()                


        except Exception as e:
            print(e)

        
    # async def upload(self):
    #     """
    #     Main coroutine to start the server.
    #     """
    #     server = await asyncio.start_server(self.handle_client, "localhost", 8888)
    #     addr = server.sockets[0].getsockname()
    #     print(f"Serving on {addr}")

    #     async with server:
    #         await server.serve_forever()

if __name__ == "__main__":
    client = TorrentSeeder(random.randint(10000, 20000))
    asyncio.run(client.seed("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/data/test/table-mountain.mp4",
                [["http://127.0.0.1:8080"]]))