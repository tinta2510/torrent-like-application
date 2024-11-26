from typing import Dict, List, Any
from fastapi import FastAPI, Request, File, UploadFile, Form, Query, HTTPException, status
from fastapi.responses import RedirectResponse, FileResponse
import configparser
import uuid
import os
import json
import click
import uvicorn
# Read configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "../config.ini")
config = configparser.ConfigParser()
config.read(CONFIG_PATH)
TORRENT_DIR = os.path.join(CURRENT_DIR, config["tracker"]["TORRENT_DIR"])
PEER_FILE = os.path.join(CURRENT_DIR, config["tracker"]["PEER_FILE"])
TORRENT_FILE = os.path.join(CURRENT_DIR, config["tracker"]["TORRENT_FILE"])
os.makedirs(TORRENT_DIR, exist_ok=True)

with open(PEER_FILE, "w") as file:
    json.dump({}, file)

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

@app.get("/")
def get_status():
    return {"status": "Tracker is running."}

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
        peer_dict = json.load(f) 

    peer_dict.setdefault(info_hash, []) 


    def update_peer_info(peer):
        """
        Function for update peer_dict

        Args:
        - peer: peer information
            Example: { "ip": <ip>, "port": <port> }
        """
        if event=="started" and peer not in peer_dict[info_hash]:
            peer_dict[info_hash].append(peer)
        elif event == 'stopped':
            peer_dict[info_hash] = [p for p in peer_dict[info_hash] if p != peer]
    
    update_peer_info({"ip": public_ip, "port": port})
    if ip:
        update_peer_info({"ip": ip, "port": port})

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

    if info_hash not in data or not os.path.exists(data[info_hash]["file_path"]):
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
        url=f"/announce?info_hash={info_hash}&port={port}&{"ip=" + ip + "&" if ip else ""}event=started", 
        status_code=302
    )

@app.get("/torrents")
async def get_all_torrents():
    with open(TORRENT_FILE, "r") as f:
        data = json.load(f)
    for key in data:
        if "file_path" in data[key]:
            del data[key]["file_path"]
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
@click.command()
@click.option("--host", 
              "-h", 
              default="127.0.0.1", 
              help=
"""The host to bind the tracker to.\n
- 127.0.0.1/localhost (default): Binds the application to localhost only.\n
- 0.0.0.0: Makes the application accessible externally on your 
local network or the internet (if no firewall blocks it).
"""
)
@click.option("--port", 
              "-p",
              default=8000,
              help="The binding port. (default: 8080)")
def main(host, port):
    """
    Start the tracker.
    """
    uvicorn.run(app=app, 
                host=host,
                port=port,
                reload=False)
    
if __name__ == "__main__":
    main()