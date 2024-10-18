import os
import bencodepy
import hashlib
import time

class MetainfoGenerator:
    """
    A class to generate metainfo (torrent) files for files or directories, based on the BitTorrent specification.

    Attributes:
        piece_length (int): The size of each file piece in bytes (default is 256KB).

    Methods:
        `_generate_file_pieces(file_path)`:
            Generate concatenated SHA-1 hashes of all file pieces for a given file.

        `_generate_file_pieces_for_directory(dir_path)`:
            Generate SHA-1 hashes for each piece of all files in a directory, treating them as a single stream of data.

        `create_metainfo_file(file_path, trackers, metainfo_dir_path=None)`:
            Create a metainfo (.torrent) file for a given file or directory, including tracker URLs.
    """
    def __init__(self, piece_length = 262144):
        """
        Initialize MetainfoGenerator with a piece_length
        
        Args:
            `piece_length` (int): The size of each piece (in byte) (default is 256KB)

        """
        self.piece_length = piece_length
        pass


    def _generate_file_pieces(self, file_path):
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
                piece = f.read(self.piece_length)  # Read a chunk of the file with size 'piece_length'
                if not piece:
                    break  
                sha1 = hashlib.sha1(piece).digest()  # Generate the SHA-1 hash of the chunk
                pieces.append(sha1)  # Append the binary SHA-1 hash to the pieces list

        return b''.join(pieces)  # Concatenate all the SHA-1 hashes and return them as a single byte string

    def _generate_file_pieces_for_directory(self, dir_path):
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
                    piece = f.read(self.piece_length)
                    if not piece:
                        break
                    sha1 = hashlib.sha1(piece).digest()
                    pieces.append(sha1)
            
            file_list.append({
                'length': os.path.getsize(file_path),
                'path': relative_path
            })

        # Traverse the directory and process each file
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, start=dir_path).split(os.sep)
                process_file(full_path, relative_path)

        return b''.join(pieces), file_list

    def create_metainfo_file(self, file_path, trackers, metainfo_dir_path = None):
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
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Invalid path: {file_path}")
        
        dir_name = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        # Torrent metadata structure
        torrent_data = {
            "announce": trackers[0],  # Primary tracker
            "announce-list": [[tracker] for tracker in trackers],  # List of trackers
            "creation date": int(time.time()),
            "info": {
                "piece length": self.piece_length,  # The length of each piece
                "name": file_name,  # Name of the file/directory
            }
        }

        # Check if it's a directory
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)

            torrent_data["info"]["length"] = file_size
            torrent_data["info"]["pieces"] = self._generate_file_pieces(file_path, self.piece_length) # Concatenated SHA-1 hashes of pieces
        else: # file_path is a directory
            pieces, file_list = self._generate_file_pieces_for_directory(file_path, self.piece_length)

            torrent_data["info"]["pieces"] = pieces
            torrent_data["info"]["files"] = file_list

        # Encode the torrent data using bencode
        encoded_data = bencodepy.encode(torrent_data)

        # Write the encoded data to a .torrent file
        torrent_file_path = f"{dir_name}/{file_name}.torrent"
        with open(torrent_file_path, 'wb') as torrent_file:
            torrent_file.write(encoded_data)

        print(f"Torrent file created: {torrent_file_path}")
        return torrent_file_path

def test():
    # Path to the file you want to share
    file_path = "D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/Like-torrent-application___/src/peer/__init__.py"

    # List of public trackers (you can add more)
    trackers = [
        "udp://tracker.leechers-paradise.org:6969/announce",
        "udp://tracker.opentrackr.org:1337/announce"
    ]

    # Create the torrent file
    metainfo_generator = MetainfoGenerator()
    metainfo_generator.create_metainfo_file(os.path.normpath(file_path), trackers)

if __name__ == "__main__":
    test()