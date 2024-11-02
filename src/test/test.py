from pathlib import Path
import logging
import bitstring
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/src')))

from torrent_peer.peer_message import BitField


print(len(BitField([0, 0, 1, 0]).encode()) )