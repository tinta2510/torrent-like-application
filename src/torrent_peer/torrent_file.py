""" Class for creating torrent file. """
import os
import hashlib
import time
from typing import List, Tuple
import bencodepy
import logging
from torrent_peer.utils import get_unique_filename
logging.basicConfig(level=logging.DEBUG)

class TorrentFile:
    """
    A class to generate metainfo (torrent) files for files or directories, based on the 
    BitTorrent specification.

    Attributes:
        piece_length (int): The size of each file piece in bytes (default is 256KB).

    Methods:
        `_generate_file_pieces(file_path)`:
            Generate concatenated SHA-1 hashes of all file pieces for a given file.

        `_generate_file_pieces_for_directory(dir_path)`:
            Generate SHA-1 hashes for each piece of all files in a directory, treating them as a 
            single stream of data.

        `create_torrent_file(file_path, trackers, metainfo_dir_path=None)`:
            Create a metainfo (.torrent) file for a given file or directory, including tracker URLs.

        `read_torrent_file
    """
    def __init__(self, filepath: str) -> None:
        if not os.path.isfile(filepath):
            raise FileNotFoundError("File not exists")
        self._filepath = filepath
    
    @property
    def files(self) -> List[Tuple[str, int]]:
        with open(self.filepath, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())
        
        info = torrent_data[b'info']
        name = info[b'name'].decode()
        file_list = info[b'files'] if b'files' in info else None
        # Extract file details if multifile
        if file_list:
            files = [(file[b'path'], file[b'length']) for file in file_list]
        else:
            return None

        paths = [(os.path.join(*[part.decode('utf-8') for part in path_parts]), length) 
                    for path_parts, length in files]
        return paths


    @property
    def info_hash(self) -> bytes:
        return TorrentFile.get_info_hash(self.filepath)

    @property
    def tracker_url(self) -> str:
        return TorrentFile.get_tracker_url(self.filepath)

    @property 
    def filepath(self) -> str:
        return self._filepath
    
    @property
    def torrent_data(self):
        """ Return decoded data from torrent file"""
        with open(self.filepath, 'rb') as file:
                # Decode the torrent file
            return bencodepy.decode(file.read())
        
    @property
    def number_of_pieces(self) -> int:
        """ Number of pieces of file """
        return len(self.torrent_data[b"info"][b"pieces"])/20 
    
    @property
    def piece_length(self) -> int:
        """ Number of bytes in each piece """
        return self.torrent_data[b"info"][b"piece length"]
    
    @property
    def filename(self) -> str:
        """ File name"""
        return self.torrent_data[b"info"][b"name"].decode("utf-8")
    
    def _generate_file_pieces(file_path: str, piece_length: str=262144):
        """
        Generate concatenated SHA-1 hashes of all file pieces.

        Args:
            `file_path`: Path to the file that is being served

        Returns:
            Concatenated SHA-1 hashes of all file pieces (in binary format)
        """
        pieces = []  # List to hold the SHA-1 hashes of each piece

        with open(file_path, 'rb') as f:  # Open the file in binary mode
            while True:
                piece = f.read(piece_length) # Read a chunk of the file with size piece_length
                if not piece:
                    break
                sha1 = hashlib.sha1(piece).digest()  # Generate the SHA-1 hash of the chunk
                pieces.append(sha1)  # Append the binary SHA-1 hash to the pieces list

        return b''.join(pieces)  # Concatenate all the SHA-1 hashes and return them as a single byte string
    
    def _generate_file_pieces_for_directory(dir_path: str, piece_length: str = 262144):
        """
        Generate SHA-1 hashes for each piece of all files in a directory.
        Concatenate files together and treat them as a single stream of data.
        
        Args:
            dir_path: Path to the directory to be shared

        Returns: 
            Concatenated SHA-1 hashes of all file pieces and file list metadata
        """
        pieces = []
        file_list = []
        total_data = b''
        # def process_file(full_path, relative_path):
        #     """
        #     Process each file by reading its data in chunks and generating SHA-1 hashes.
        #     """
        #     with open(full_path, 'rb') as f:
        #         while True:
        #             piece = f.read(piece_length)
        #             if not piece:
        #                 break
        #             sha1 = hashlib.sha1(piece).digest()
        #             pieces.append(sha1)         
        #     file_list.append({
        #         'length': os.path.getsize(full_path),
        #         'path': relative_path
        #     })

        # Traverse the directory and process each file
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, start=dir_path).split(os.sep)
                # process_file(full_path, relative_path)
                file_list.append({
                    'length': os.path.getsize(full_path),
                    'path': relative_path
                })

                # Process each file by reading its data in chunks and generating SHA-1 hashes.
                with open(full_path, 'rb') as f:
                    while True:
                        piece = f.read(piece_length)
                        if not piece:
                            break
                        total_data += piece
                        if len(total_data) >= piece_length:
                            sha1 = hashlib.sha1(total_data[:piece_length]).digest()
                            pieces.append(sha1) 
                            total_data = total_data[piece_length:]
        if len(total_data) > 0:
            sha1 = hashlib.sha1(total_data).digest()
            pieces.append(sha1)
        
        return b''.join(pieces), file_list

    @classmethod
    def create_torrent_file(cls, input_path: str, trackers: List[List[str]], piece_length: int = 262144, output_path: str = None):
        """
        Create a metainfo (.torrent) file for the given file. 
        See http://bittorrent.org/beps/bep_0003.html for more.

        Args:
            `file_path` (string): The path to the file to be serverd.
            `trackers` ([string]): A list of tracker URLs.
            `metainfo_dir_path` (string): The path to the directory to contain created metainfo file. 
                (default is None, which means the file is at the same directory as the served file)

        Returns:
            `metainfo_filepath` (string): The path to the created metainfo file.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Invalid path: {input_path}")
        
        dir_name = os.path.dirname(input_path)
        file_name = os.path.basename(input_path)
        
        # Torrent metadata structure
        torrent_data = {
            "announce": trackers[0][0],  # Primary tracker
            "announce-list": [[tracker] for tracker in trackers],  # List of trackers
            "creation date": int(time.time()),
            "info": {
                "piece length": piece_length,  # The length of each piece
                "name": file_name,  # Name of the file/directory
            }
        }

        # Check if it's a directory
        if os.path.isfile(input_path):
            file_size = os.path.getsize(input_path)

            torrent_data["info"]["length"] = file_size
            torrent_data["info"]["pieces"] = cls._generate_file_pieces(input_path, piece_length) # Concatenated SHA-1 hashes of pieces
        else: # file_path is a directory
            pieces, file_list = cls._generate_file_pieces_for_directory(input_path, piece_length)

            torrent_data["info"]["pieces"] = pieces
            torrent_data["info"]["files"] = file_list

        # Encode the torrent data using bencode
        encoded_data = bencodepy.encode(torrent_data)

        # Write the encoded data to a .torrent file
        output_path = output_path or f"{dir_name}/{file_name}.torrent"
        output_path = get_unique_filename(output_path)
        with open(output_path, 'wb') as torrent_file:
            torrent_file.write(encoded_data)

        print(f"Torrent file created: {output_path}")
        return output_path

    @classmethod
    def get_info_hash(cls, torrent_filepath: str) -> bytes:
        """
        Reads a torrent file, extracts the 'info' dictionary, and calculates the SHA-1 info_hash.
        
        Args:
            torrent_file_path (str): The path to the .torrent file.
        
        Returns:
            str: The hexadecimal representation of the info_hash.
        
        Raises:
            FileNotFoundError: If the specified file does not exist.
            bencodepy.DecoderError: If the file is not in a valid Bencoded format.
        """
        try:
            with open(torrent_filepath, 'rb') as file:
                # Decode the torrent file
                torrent_data = bencodepy.decode(file.read())
                
            # Extract the 'info' dictionary
            info_dict = torrent_data[b'info']

            # Compute SHA-1 hash of the Bencoded 'info' dictionary
            info_hash = hashlib.sha1(bencodepy.encode(info_dict)).digest()
            
            return info_hash

        except FileNotFoundError:
            raise FileNotFoundError(f"The file '{torrent_filepath}' does not exist.")
        except bencodepy.DecodingError:
            raise ValueError("The file is not in a valid Bencoded format.")

    @classmethod 
    def get_tracker_url(cls, torrent_filepath: str) -> str:
        try:
            with open(torrent_filepath, 'rb') as file:
                # Decode the torrent file
                torrent_data = bencodepy.decode(file.read())
                tracker_url = torrent_data[b"announce"].decode('utf-8')  
                return tracker_url
        except FileNotFoundError:
            raise FileNotFoundError(f"The file '{torrent_filepath}' does not exist.")
        except bencodepy.DecodingError:
            raise ValueError("The file is not in a valid Bencoded format.")
# End-of-file (EOF)