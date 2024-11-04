import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/src')))

from torrent_peer.torrent_file import TorrentFile

torrent = TorrentFile("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/data/sample.torrent")

print(torrent.piece_length  )