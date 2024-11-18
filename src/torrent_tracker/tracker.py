from typing import Dict, List, Any
from fastapi import FastAPI, Request, File, UploadFile, Form, Query, HTTPException, status
from fastapi.responses import RedirectResponse, FileResponse
import configparser
import uuid
import os
import json

# Read configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
TORRENT_DIR = os.path.join(CURRENT_DIR, config["tracker"]["TORRENT_DIR"])
PEER_FILE = os.path.join(CURRENT_DIR, config["tracker"]["PEER_FILE"])
TORRENT_FILE = os.path.join(CURRENT_DIR, config["tracker"]["TORRENT_FILE"])

# with open(PEER_FILE, 'w') as file:
#     file.write('{}')
# with open(TORRENT_FILE, 'w') as file:
#     file.write('{}')

app = FastAPI()

# Exception response
class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class BadRequestError(HTTPException):
    def __init__(self, detail: str = "Bad Request Error."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

# Function to get peers
def get_peers(peer_dict, info_hash: str) -> List[Dict[str, str]]:
    """
    Retrieve the list of peers for a given info_hash.
    """
    return [
        {
            "ip": peer["ip"], 
            "port": peer["port"]
        } for peer in peer_dict.get(info_hash, [])
    ]

@app.get("/announce")
async def announce(
    request: Request, 
    info_hash: (str) = Query(...), 
    port: int = Query(...), 
    ip: str = Query(None),
    event: str = Query(None)
):
    public_ip = request.client.host # Get client IP
    with open(PEER_FILE, "r") as f:
        peer_dict: Dict[str, List[Any]] = json.load(f) 

    peer_dict.setdefault(info_hash, []) 

    # Update peer information
    peer = {"ip": public_ip, "port": port}
    if event=="started" and peer not in peer_dict[info_hash]:
        peer_dict[info_hash].append(peer)
    elif event == 'stopped':
        peer_dict[info_hash] = [p for p in peer_dict[info_hash] if p != peer]
    
    # Update peer information in case a local ip is sent
    if ip:
        peer_2 = {"ip": ip, "port": port}
        if event=="started" and peer_2 not in peer_dict[info_hash]:
            peer_dict[info_hash].append(peer_2)
        elif event == 'stopped':
            peer_dict[info_hash] = [p for p in peer_dict[info_hash] if p != peer_2]

    # Respond with a list of peers for this torrent
    peers = get_peers(peer_dict, info_hash)
    with open(PEER_FILE, 'w') as f:
        json.dump(peer_dict, f, indent=4)
    response = {"interval": 1800, "peers": peers}  # 'interval' is in seconds
    return response

@app.post("/announce")
async def insert_torrent(
    file: UploadFile = File(...),
    name: str = Form(""),
    description: str = Form(""),
    info_hash: str = Query(...),
    port: int = Query(...),
    ip: str = Query(None),
):
    # Check if the file has a .torrent extension
    if not file.filename.endswith(".torrent"):
        raise BadRequestError("Accept file with .torrent file extension only.")

    with open(TORRENT_FILE, "r") as f:
        data = json.load(f) 

    if info_hash not in data:
        file_path = os.path.join(TORRENT_DIR, f"{uuid.uuid4()}.torrent")
        with open(file_path, "wb") as f:
            f.write(await file.read())

        name = name + ".torrent" if name else file.filename

        data[info_hash] = {
            "file_path": file_path,
            "name": name,
            "description": description,
        }

        with open(TORRENT_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    return RedirectResponse(
        url=f"/announce?info_hash={info_hash}&port={port}&{f"ip={ip}&" if ip else ""}event=started", 
        status_code=302
    )

@app.get("/torrents")
async def get_all_torrents():
    with open(TORRENT_FILE, "r") as f:
        data = json.load(f)
    return data

@app.get("/torrents/{info_hash}")
async def get_torrent_by_info_hash(info_hash: str):
    with open(TORRENT_FILE, "r") as f:
        data = json.load(f)

    if info_hash not in data or not os.path.exists(data[info_hash]["file_path"]):
        raise BadRequestError(
            detail=f"Bad Request: {info_hash} not found"
        )

    return FileResponse(
        path = data[info_hash]["file_path"],
        filename = data[info_hash]["name"],
        media_type= "application/octet-stream"
    )
