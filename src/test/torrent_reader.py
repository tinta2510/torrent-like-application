from torrentool.api import Torrent
import pprint
torrent = Torrent.from_file("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/data/sample.torrent")
pprint.pprint(torrent._struct)