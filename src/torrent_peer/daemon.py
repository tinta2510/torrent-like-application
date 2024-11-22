from quart import Quart, request, jsonify
import os
from random import randint
import asyncio
import logging
from torrent_peer.peer import TorrentPeer
from torrent_peer.config_loader import TORRENT_DIR, DOWNLOAD_DIR, LOG_DIR, TRACKER_URL

os.makedirs(TORRENT_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=f'./{LOG_DIR}/logfile.log',  # Name of the log file
    level=logging.DEBUG,     # Log all levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

app = Quart(__name__)
peer = TorrentPeer(randint(1025, 60000))

@app.route("/")
def get_server_status():
    return jsonify({"status": "OK"}), 200

@app.route("/status")
def get_status():
    status = {}

    status["seeding"] =[[
            info_hash, 
            value["filepath"]
        ] for info_hash, value in peer.seeding_torrents.items()]
    status["leeching"] = [[
            info_hash, 
            piece_manager.output_name, 
            piece_manager.percent_of_downloaded
        ] for info_hash, piece_manager in peer.leeching_torrents.items()]
    return jsonify(status), 200

@app.route("/seed", methods=["POST"])
async def seed():
    try:
        data = await request.get_json()    
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
        return jsonify({"message": f"Start seeding {input_path}"}), 200
    except FileNotFoundError as e:
        return jsonify({"error": "File not found error.",
                        "details": f"{input_path} doesn't exist"}), 400
    except Exception as e:
        return jsonify({"error": e}), 500
    
@app.route("/leech", methods=["POST"])  
async def leech():
    data = await request.get_json()
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
    return jsonify({"message": "File is downloading."}), 200

@app.route("/torrents", methods=["GET"])
async def get_torrents():
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

@app.before_serving
async def run_background_tasks():
    # Start peer tasks
    logging.info("Start peer tasks.")
    asyncio.create_task(peer.start_seeding())
    asyncio.create_task(peer.start_leeching())

def main():
    try:
        app.run(port=randint(1025, 5000))
    except KeyboardInterrupt:
        logging.info("Catch Ctrl+C")

if __name__ == '__main__':
    main()