from pathlib import Path
import logging
import bitstring
import sys
import os
import pprint
import struct
from math import ceil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/src')))
from torrent_peer.torrent_file import TorrentFile


import socket
import socket
import uuid


torrent =  Path("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/src/peer_v2/torrents/table-mountain.mp4_1.torrent").stem
print(torrent)



