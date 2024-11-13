import os
from pprint import pprint
from torrent_peer.torrent_file import TorrentFile

path = TorrentFile.create_torrent_file("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/src/torrent_tracker", [["http://tinta.com"]])
torrent = TorrentFile(path)

pprint(torrent.files)