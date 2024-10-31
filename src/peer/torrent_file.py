""" Class for creating torrent file. """
import os
import hashlib
import time
from typing import List
import bencodepy

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
    @staticmethod
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
    
    @staticmethod
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

        def process_file(file_path, relative_path):
            """
            Process each file by reading its data in chunks and generating SHA-1 hashes.
            """
            with open(file_path, 'rb') as f:
                while True:
                    piece = f.read(piece_length)
                    if not piece:
                        break
                    sha1 = hashlib.sha1(piece).digest()
                    pieces.append(sha1)         
            file_list.append({
                'length': os.path.getsize(file_path),
                'path': relative_path
            })

        # Traverse the directory and process each file
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, start=dir_path).split(os.sep)
                process_file(full_path, relative_path)

        return b''.join(pieces), file_list

    @staticmethod
    def create_torrent_file(input_path: str, trackers: List[List[str]], piece_length: int = 262144, output_path: str = None):
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
            torrent_data["info"]["pieces"] = TorrentFile._generate_file_pieces(input_path, piece_length) # Concatenated SHA-1 hashes of pieces
        else: # file_path is a directory
            pieces, file_list = TorrentFile._generate_file_pieces_for_directory(input_path, piece_length)

            torrent_data["info"]["pieces"] = pieces
            torrent_data["info"]["files"] = file_list

        # Encode the torrent data using bencode
        encoded_data = bencodepy.encode(torrent_data)

        # Write the encoded data to a .torrent file
        output_path = output_path if output_path else f"{dir_name}/{file_name}.torrent"
        with open(output_path, 'wb') as torrent_file:
            torrent_file.write(encoded_data)

        print(f"Torrent file created: {output_path}")
        return output_path

    @staticmethod
    def get_info_hash(torrent_filepath: str) -> str:
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
                info_hash = hashlib.sha1(bencodepy.encode(info_dict)).hexdigest()
                
                return info_hash

        except FileNotFoundError:
            raise FileNotFoundError(f"The file '{torrent_filepath}' does not exist.")
        except bencodepy.DecodingError:
            raise ValueError("The file is not in a valid Bencoded format.")

print(TorrentFile.get_info_hash("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/data/sample.torrent"))
# End-of-file (EOF)