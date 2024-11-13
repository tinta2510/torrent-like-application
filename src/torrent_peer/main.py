import random
import threading
import asyncio
import os
import configparser

from torrent_peer.peer import TorrentPeer

# READ data from configuration file 
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
TRACKER_URL = config["peer"]["TRACKER_URL"]
TORRENT_DIR = os.path.join(CURRENT_DIR, config["peer"]["TORRENT_DIR"])
DOWNLOAD_DIR = os.path.join(CURRENT_DIR, config["peer"]["DOWNLOAD_DIR"])

async def user_function(peer: TorrentPeer, stop_event):
    try: 
        while not stop_event.is_set():
            flag = input("Choost option seed/leech (s/l): ")
            if (flag == "s"):
                path = input("Give a file to seed.")
                peer.seed(path, [[TRACKER_URL]])
            elif (flag == "l"):
                torrent_filepath = TorrentPeer.get_torrent()
                await peer.download(torrent_filepath)
            else: 
                print("Choose 's' or 'l' only.")
    except KeyboardInterrupt as e:
        stop_event.set()
        print("Catch Ctrl+C at user_function")
    except Exception as e:
        stop_event.set()
        print("Catch exception at user_function", e)

def main():
    try: 
        peer = TorrentPeer(random.randint(1025, 60000))
        stop_event = threading.Event()
        seeding_thread = threading.Thread(target=lambda peer, stop_event: asyncio.run(peer.start(stop_event)), args=(peer, stop_event))
        user_thread = threading.Thread(target=lambda peer, stop_event: asyncio.run(user_function(peer, stop_event)), args=(peer, stop_event))

        seeding_thread.start()
        user_thread.start()

        seeding_thread.join()
        user_thread.join()
    except KeyboardInterrupt as e:
        stop_event.set()
        print("Catch Ctrl+C at main")
    except Exception as e:
        print("Catch exception at main", e)  

if __name__ == "__main__":
    main()