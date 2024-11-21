import os
import configparser

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
TRACKER_URL = config["peer"]["TRACKER_URL"]
TORRENT_DIR = os.path.join(CURRENT_DIR, config["peer"]["TORRENT_DIR"])
DOWNLOAD_DIR = os.path.join(CURRENT_DIR, config["peer"]["DOWNLOAD_DIR"])
LOG_DIR = os.path.join(CURRENT_DIR, config["peer"]["LOG_DIR"])
INTERVAL = int(config["peer"]["INTERVAL"])
