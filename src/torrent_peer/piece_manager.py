from peer_v2.torrent_file import TorrentFile
from typing import List, Dict, Any
from bitstring import BitArray
from math import ceil
import struct
import logging
import configparser
from peer_v2.peer_message import Request, Piece, PeerMessage

logging.basicConfig(level=logging.DEBUG)

# Create a parser
config = configparser.ConfigParser()
# Read the config file
config.read('../config.ini')

class PieceManager:
    def __init__(self, torrent: TorrentFile, output_path: str) -> None:
        self.torrent: TorrentFile = torrent
        # Current downloaded pieces
        self.had_pieces: List[bool] = [False for i in range(int(self.torrent.number_of_pieces))] 
        self.pending_pieces: List[bool] = [False for i in range(int(self.torrent.number_of_pieces))]
        self.connected_peers = {}
        self.completed = False
        self.output_path: str = output_path
        
        with open(output_path, "wb") as file:
            file.truncate(self.torrent.torrent_data[b"info"][b"length"])

    def get_request_msg(self) -> Request:
        for i, value in enumerate(self.had_pieces):
            if (value == False) and self.pending_pieces[i] == False:
                self.pending_pieces[i] = True
                if i == self.torrent.number_of_pieces - 1:
                    requested_length = self.torrent.torrent_data[b"info"][b"length"] \
                                        % self.torrent.piece_length 
                    return Request(i, 0, requested_length).encode()
                return Request(i, 0, self.torrent.piece_length).encode()

    def receive_piece(self, piece: bytes, length: int):
        (id, index, begin) = struct.unpack(f'>bII', piece[:9])
        # logging.debug( (id, index, begin, len(piece[9:])))
        if (id != PeerMessage.Piece):
            raise Exception("Not a valid Piece!")
        
        with open(self.output_path, "rb+") as file:
            file.seek(index * self.torrent.piece_length)
            file.write(piece[9:])

        self.had_pieces[index] = True
        self.pending_pieces[index] = False
        self.completed = all(self.had_pieces)
