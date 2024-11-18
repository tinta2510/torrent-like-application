import random
from threading import Thread, Event
import asyncio
import os
import configparser
from concurrent.futures import ThreadPoolExecutor

from torrent_peer.peer import TorrentPeer
from torrent_peer.torrent_file import TorrentFile
# READ data from configuration file 
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
TRACKER_URL = config["peer"]["TRACKER_URL"]
TORRENT_DIR = os.path.join(CURRENT_DIR, config["peer"]["TORRENT_DIR"])
DOWNLOAD_DIR = os.path.join(CURRENT_DIR, config["peer"]["DOWNLOAD_DIR"])

def print_status(peer: TorrentPeer, stop_event: Event):
    while not stop_event.is_set():
        print("Seeding: ")
        for info_hash in peer.seeding_torrents:
            print(info_hash)

async def user_interact(peer: TorrentPeer, stop_event: Event):
    try: 
        executor = ThreadPoolExecutor(max_workers=3)
        stop_events = {}
        stop_printing_event = Event()
        while not stop_event.is_set():
            flag = input("Choost option seed/leech (s/l/status): ")
            if (flag == "s"):
                path = input("Give a file to seed:")
                peer.seed(path, [[TRACKER_URL]])
            elif (flag == "l"):
                torrent_filepath = TorrentPeer.get_torrent()
                info_hash = TorrentFile.get_info_hash(torrent_filepath)
                stop_events[info_hash] = Event()
                executor.submit(asyncio.run, peer.download(torrent_filepath, stop_events[info_hash]))
            elif (flag == "status"): 
                stop_printing_event.clear()
                printing_thread = Thread(target=print_status, args=(peer,stop_printing_event))
                printing_thread.start()
            else: 
                print("Choose 's' or 'l' only.")
    except KeyboardInterrupt as e:
        print("Catch Ctrl+C at user_function")
    except Exception as e:
        print("Catch exception at user_function", e)
    finally: 
        stop_printing_event.set()
        executor.shutdown(False)
        stop_event.set()

def main():
    try: 
        # Create a peer
        peer = TorrentPeer(random.randint(1025, 60000))
        stop_event = Event()

        seeding_thread = Thread(target=lambda peer, stop_event: asyncio.run(peer.start(stop_event)), 
                                args=(peer, stop_event))
        user_thread = Thread(target=lambda peer, stop_event: asyncio.run(user_interact(peer, stop_event)), 
                             args=(peer, stop_event))

        seeding_thread.start()
        user_thread.start()

        seeding_thread.join()
        user_thread.join()
    except KeyboardInterrupt as e:
        stop_event.set()
        print("Catch Ctrl+C at main")
    except Exception as e:
        stop_event.set()
        print("Catch exception at main", e)  

if __name__ == "__main__":
    main()