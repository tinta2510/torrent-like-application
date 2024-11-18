from torrent_peer.torrent_file import TorrentFile
from typing import List, Dict, Any
import struct
import logging
import configparser
import os
from torrent_peer.peer_message import Request, PeerMessage
from enum import Enum
import hashlib

from torrent_peer.utils import get_unique_filename

# logging.basicConfig(level=logging.INFO)

# Create a parser
config = configparser.ConfigParser()
# Read the config file
config.read('../config.ini')

class PieceStatus(Enum):
    EMPTY = 0
    PENDING = 1
    DOWNLOADED = 2

class PieceManager:
    def __init__(self, torrent: TorrentFile, output_dir: str) -> None:
        self.torrent: TorrentFile = torrent
        self.pieces_status: List[int] = [PieceStatus.EMPTY for _ in range(int(self.torrent.number_of_pieces))] 
        self.completed = False
        self.output_name: str = get_unique_filename(
            os.path.join(output_dir, self.torrent.torrent_data[b"info"][b"name"].decode("utf-8"))
        )
        self.haveMultiFile =  True if torrent.files else False

        if self.haveMultiFile: # In case of multi files
            # Calculate file offset + total length
            self.file_limit = []
            self.total_length = 0
            for (path, length) in torrent.files:
                self.total_length += length
                self.file_limit.append((path, length, self.total_length))

            os.makedirs(self.output_name, exist_ok=True) 
            for (rel_path, length) in torrent.files: 
                filepath = os.path.join(self.output_name, rel_path)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as file:
                    file.truncate(length)
        else:
            length = self.torrent.torrent_data[b"info"][b"length"]
            with open(self.output_name, "wb") as file:
                file.truncate(length)

    def get_request_msg(self) -> Request:
        piece_length = self.torrent.piece_length
        length = self.total_length if self.haveMultiFile \
                else self.torrent.torrent_data[b"info"][b"length"]

        for i, value in enumerate(self.pieces_status):
            if value == PieceStatus.EMPTY:
                self.pieces_status[i] = PieceStatus.PENDING
                if i == self.torrent.number_of_pieces - 1:
                    requested_length = length % piece_length  
                    return Request(i, 0, requested_length).encode()
                return Request(i, 0, piece_length).encode()
            
    def validate_received_piece(self, piece_data, index):
        expected_hash = self.torrent.torrent_data[b"info"][b"pieces"][index*20:index*20 + 20]
        hashed_data = hashlib.sha1(piece_data).digest() 
        return expected_hash == hashed_data

    def receive_piece(self, piece: bytes):
        piece_length = self.torrent.piece_length
        (id, index, begin) = struct.unpack(f'>bII', piece[:9])
        data = piece[9:]        

        if (id != PeerMessage.Piece):
            raise Exception("Not a valid Piece!")
        if not self.validate_received_piece(data, index):
            raise Exception("Not expected piece.")
        logging.debug("Valid piece")
        if self.haveMultiFile:
            logging.debug("Checkpoint")
            lower_offset = index * piece_length
            upper_offset = lower_offset + len(data) - 1
            curr = 0
            for (path, file_length, upper_limit) in self.file_limit:
                logging.debug("Loop check")
                if lower_offset + curr >= upper_limit:
                    continue
                writing_position = lower_offset + curr - upper_limit + file_length
                if upper_offset < upper_limit:
                    with open(os.path.join(self.output_name, path), "rb+") as file:
                        file.seek(writing_position)
                        file.write(data[curr:])
                    logging.debug(f"Write to {path} at {writing_position} with length {len(data[curr:])}")
                    break
                else:
                    writing_length = upper_limit - (lower_offset + curr)
                    with open(os.path.join(self.output_name, path), "rb+") as file:
                        file.seek(writing_position)
                        file.write(data[curr:curr+writing_length])
                    logging.debug(f"Write to {path} at {writing_position} with length {writing_length}")
                    curr += writing_length     
        else:
            with open(self.output_name, "rb+") as file:
                file.seek(index * self.torrent.piece_length)
                file.write(data)

        self.pieces_status[index] = PieceStatus.DOWNLOADED
        self.completed = all([x == PieceStatus.DOWNLOADED for x in self.pieces_status])
 