from flask import Flask, request, jsonify
import os
import configparser
from random import randint
from threading import Thread, Event
import asyncio
import requests
import logging
from torrent_peer.utils import get_unique_filename
from torrent_peer.peer import TorrentPeer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
TRACKER_URL = config["peer"]["TRACKER_URL"]
TORRENT_DIR = os.path.join(CURRENT_DIR, config["peer"]["TORRENT_DIR"])
DOWNLOAD_DIR = os.path.join(CURRENT_DIR, config["peer"]["DOWNLOAD_DIR"])

app = Flask(__name__)

peer = TorrentPeer(randint(1025, 60000))

@app.route("/", methods=["GET"])
def status():
    return jsonify({"status": "OK"}), 200

@app.route("/seed", methods=["POST"])
def seed():
    try:
        data = request.get_json()    
        input_path = data.get("input_path", None)
        if input_path is None:
            return jsonify({"error": "input_path is required"}), 400
        peer.seed(
            input_path = input_path,
            trackers= data.get("trackers", [[TRACKER_URL]]),
            public=data.get("public", True),
            piece_length=data.get("piece_length", None),
            torrent_filepath=data.get("torrent_filepath", None),
            name=data.get("name", ""),
            description=data.get("description", "")
        )
        return jsonify({"message": "Seeding started"}), 200
    except FileNotFoundError as e:
        return jsonify({"error": "File not found error.",
                        "details": f"{input_path} doesn't exist"}), 400
    except Exception as e:
        return jsonify({"error": e}), 500
    
@app.route("/leech", methods=["POST"])  
async def leech():
    data = request.get_json()
    torrent_filepath = data.get("torrent_filepath", None)
    if not torrent_filepath:
        return jsonify({
            'error': "Missing required parameters",
            "missing": "torrent_filepath"
        }), 400
    if not os.path.exists(torrent_filepath):
        return jsonify({
            'error': "File not found error.",
            'details': "Torrent File not exists."
        }), 400
    await peer.torrent_queue.put(torrent_filepath)
    return jsonify({"message": "Added file to be downloaded successfully"}), 200

@app.route("/torrents", methods=["GET"])
def get_torrents():
    try:
        torrents = TorrentPeer.get_torrents()
        return jsonify({"data": torrents}), 200
    except RuntimeError as e:
        # Catch custom errors raised from get_torrents
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        # Catch-all for any other unanticipated exceptions
        logging.error(f"Unexpected error: {e}")  # Log the error for debugging
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route("/torrents/<string:info_hash>", methods=["GET"])
def get_torrent_by_info_hash(info_hash):
    try:
        file_path = TorrentPeer.get_torrent_by_info_hash(info_hash)
        return jsonify({"data": file_path}), 200
    except Exception as e:
        # Catch-all for any other unanticipated exceptions
        logging.error(f"Unexpected error: {e}")  # Log the error for debugging
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

async def start_peer(peer: TorrentPeer, stop_event: Event):
    seeding = asyncio.create_task(peer.start_seeding(stop_event))
    leeching = asyncio.create_task(peer.start_leeching(stop_event))

    await asyncio.gather(seeding, leeching)

if __name__ == '__main__':
    stop_event = Event()
    peer_thread = Thread(
        target=lambda peer, stop_event: asyncio.run(start_peer(peer, stop_event)),
        args=(peer, stop_event)
    )

    try:
        peer_thread.start()
        app.run(port=randint(1024, 50000))
    finally:
        stop_event.set()
        peer_thread.join()
