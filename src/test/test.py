import filecmp
import os
from torrent_peer.torrent_file import TorrentFile
# def files_are_identical(file1, file2):
#     return filecmp.cmp(file1, file2, shallow=False)

# # print(files_are_identical(r"D:\HCMUT_Workspace\HK241\Computer-Networks\Assignment-1\torrent-like-application\data\test\table-mountain.mp4", 
# #                           r"D:\HCMUT_Workspace\HK241\Computer-Networks\Assignment-1\torrent-like-application\src\torrent_peer\downloads\data_3\test\table-mountain.mp4"))

# file1 = r"D:\HCMUT_Workspace\HK241\Computer-Networks\Assignment-1\torrent-like-application\data\test\table-mountain.mp4"
# file2 = r"D:\HCMUT_Workspace\HK241\Computer-Networks\Assignment-1\torrent-like-application\src\torrent_peer\downloads\data\test\table-mountain.mp4"

# with open(file1, "rb") as f:
#     f.seek(10000)
#     data = f.read(5000)
#     print("File1: ", data)

# with open(file2, "rb") as f:
#     f.seek(10000)
#     data = f.read(5000)
#     print("file2: ", data)

torrent = TorrentFile(r"D:\HCMUT_Workspace\HK241\Computer-Networks\Assignment-1\torrent-like-application\src\torrent_peer\torrents\data.torrent")
print(torrent.files)