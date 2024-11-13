from peer_v2.torrent_file import TorrentFile
from enum import Enum

class TorrentManager:
    def __init__(self):
        self.torrents = {}

    def insert_torrent(self, info_hash: str, torrent: TorrentFile, file_path: str):
        '''
        Class for managing uploading and downloading files.
        Args:
            info_hash (str): info_hash of file.
            torrent (TorrentFile): Keep track the file torrent file.
            file_path (str): source filepath.
        '''
        if info_hash in self.torrents:
            raise FileExistsError("File already in torrent list")
        
        self.torrents[info_hash] = {
            "torrent": torrent,
            
        }
