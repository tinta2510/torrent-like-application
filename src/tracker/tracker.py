from typing import Dict, List
from fastapi import FastAPI, Request, Response, File, UploadFile, Form, Query, HTTPException,\
                     status
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from pydantic import BaseModel
import configparser
import uuid
import os
import json
# Create a parser
config = configparser.ConfigParser()
# Read the config file
config.read('../../config.ini')
UPLOADED_DIRECTORY = config["tracker"]["UPLOADED_DIRECTORY"]
PEERS_FILE = config["tracker"]["PEERS_FILE"]
TORRENTS_FILE = config["tracker"]["TORRENTS_FILE"]

app = FastAPI()

class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

# Store peers information in memory
def get_peers(peer_dict, info_hash: str) -> List[Dict[str, str]]:
    """
    Retrieve the list of peers for a given info_hash.
    """
    if info_hash in peer_dict:
        return [{"ip": peer["ip"], "port": peer["port"]} for peer in peer_dict[info_hash]]
    return []

@app.get("/announce")
async def announce(
    request: Request, 
    info_hash: (str) = Query(...), 
    port: int = Query(...), 
    ip: str = Query(None),
    event: str = Query(None)
) -> None:
    ip = request.client.host # Get client IP
    with open(PEERS_FILE, "r") as f:
        peer_dict = json.load(f) 
    # Register peer in the list for the specific info_hash
    if info_hash not in peer_dict:
        peer_dict[info_hash] = []

    # Update or add peer information
    peer = {"ip": ip, "port": port}
    if peer not in peer_dict[info_hash] and event=="started":
        peer_dict[info_hash].append(peer)

    # Handle 'stopped' event to remove peer
    if event == 'stopped':
        peer_dict[info_hash] = [p for p in peer_dict[info_hash] if p != peer]
    

    # Respond with a list of peers for this torrent
    peers = get_peers(peer_dict, info_hash)
    with open(PEERS_FILE, 'w') as f:
        json.dump(peer_dict, f, indent=4)
    response = {"interval": 1800, "peers": peers}  # 'interval' is in seconds

    return response

@app.post("/announce")
async def insert_torrent(
    request: Request, 
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(None),
    info_hash: str = Query(...),
    port: int = Query(...),
    ip: str = Query(None),
) -> None:
    with open(TORRENTS_FILE, "r") as f:
        data = json.load(f) 

    if info_hash not in data:
        file_path = os.path.join(UPLOADED_DIRECTORY, str(uuid.uuid4()))
        with open(file_path, "wb") as f:
            f.write(await file.read())

        data[info_hash] = {
            "file_path": file_path,
            "name": name,
            "description": description,
        }

        with open(TORRENTS_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    return RedirectResponse(url=f"/announce?info_hash={info_hash}&port={port}&{f"ip={ip}&" if ip else ""}event=started", status_code=302)

@app.get("/torrents")
async def get_all_torrents():
    with open(TORRENTS_FILE, "r") as f:
        data = json.load(f)
    return data

@app.get("/torrents/{info_hash}")
async def get_torrent_by_info_hash(info_hash: str):
    with open(TORRENTS_FILE, "r") as f:
        data = json.load(f)

    if info_hash not in data:
        raise NotFoundError(f"Torrent with {info_hash=} not found.")

    return FileResponse(
        path = data[info_hash]["file_path"],
        filename = data[info_hash]["name"],
        media_type= "application/octet-stream"
    )
# @app.get("/torrents")
# async def get_all_torrents(request: Request,)
