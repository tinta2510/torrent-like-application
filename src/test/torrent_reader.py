import bencodepy 
import pprint

# Give the path to the torrent file that you want to read
with open("D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/Like-torrent-application___/data/sample.torrent", "rb") as file: 
    content = bencodepy.decode(file.read())

pprint.pprint(content)