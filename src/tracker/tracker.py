from flask import Flask, request, jsonify
from typing import Dict, List
import hashlib

app = Flask(__name__)

# Store peers information in memory
torrents = {}

def get_peer_list(info_hash: str) -> List[Dict[str, str]]:
    """
    Retrieve the list of peers for a given info_hash.
    """
    if info_hash in torrents:
        return [{"ip": peer["ip"], "port": peer["port"]} for peer in torrents[info_hash]]
    return []

@app.route('/announce', methods=['GET'])
def announce():
    # Parse query parameters
    info_hash = request.args.get('info_hash')
    peer_id = request.args.get('peer_id')
    port = request.args.get('port')
    event = request.args.get('event')
    ip = request.remote_addr  # Get client IP

    if not (info_hash and peer_id and port):
        return jsonify({"error": "Missing required parameters"}), 400

    # Register peer in the list for the specific info_hash
    if info_hash not in torrents:
        torrents[info_hash] = []

    # Update or add peer information
    peer = {"peer_id": peer_id, "ip": ip, "port": port}
    if peer not in torrents[info_hash]:
        torrents[info_hash].append(peer)

    # Handle 'stopped' event to remove peer
    if event == 'stopped':
        torrents[info_hash] = [p for p in torrents[info_hash] if p["peer_id"] != peer_id]

    # Respond with a list of peers for this torrent
    peers = get_peer_list(info_hash)
    response = {"interval": 1800, "peers": peers}  # 'interval' is in seconds

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
