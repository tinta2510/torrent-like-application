from torrent_file import TorrentFile
from typing import List

class PieceManager:
    def __init__(self, torrent: TorrentFile) -> None:
        self.torrent: TorrentFile = torrent
        # initialize bitfield array
        self.bitfield: List[int] = [0] * len(self.torrent.torrent_data[b"info"]["pieces"])/20 

