# Torrent-like application
## Overview
This project implements a simple BitTorrent-like P2P file-sharing system to enable scalable and decentralized file sharing, including both a tracker and peer functionalities. It allows users to seed and leech files, manage torrents, and interact with a tracker for peer discovery.

- **Tracker**: Acts as a coordinator by storing .torrent meta-info files and maintaining a dynamic list of peers. It helps leechers discover seeders without hosting the actual file content.

- **Peers**: Each peer can simultaneously seed and leech files. Files are split into fixed-size pieces, validated by SHA1 hashes to ensure data integrity. After downloading, a peer automatically switches to seeding mode, enhancing swarm availability.

- **Meta-info File (.torrent)**: Encodes metadata using bencoding, including file info, piece hashes, and tracker URLs. This file guides peers in retrieving the file from others.

- **Protocols**:

  - HTTP (Tracker Communication): Peers announce their status and retrieve peer lists using GET/POST requests.

  - TCP (Peer-to-Peer): Peers exchange file pieces using a lightweight binary protocol starting with a handshake.
## Features

### Tracker
- **Peer List Management**: Maintains a list of peers for each torrent.
- **Meta-info File Storage**: Stores `.torrent` files and metadata for torrents.

### Peer
- **Seeding**: Uploading (seeding) multi-file torrents.
- **Leeching**: Downloading (leeching) multi-file torrents.
- **Simultaneous Operations**: Supports downloading and uploading multiple torrents simultaneously.
- **Piece Management**: Handles pieces of files during download and upload.
- **Piece Validation**: Ensures data integrity by validating pieces.
- **Status Monitoring**: Provides uploading and downloading status.
- **Auto-Seeding**: Automatically starts seeding after downloading a file.

---

## Usage

### 1. Clone the Repository
```bash
git clone https://github.com/tinta2510/torrent-like-application.git
```

### 2. Install the Package
Navigate to the `src` directory and install the package along with its dependencies:
```bash
cd torrent-like-application/src
pip install .
```

### 3. (Optional) Set Up a Virtual Environment
To avoid conflicts with existing Python packages, you can set up a virtual environment:
1. Create a virtual environment:
   ```bash
   python -m venv env_name
   ```
2. Activate the virtual environment:
   - On Windows:
     ```bash
     env_name\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source env_name/bin/activate
     ```
3. Verify the activation:
   ```bash
   python --version
   ```
4. Deactivate when done:
   ```bash
   deactivate
   ```
---

## Configuration
Edit the `config.ini` file in the `src` directory to customize the application settings:

### Tracker Configuration
- `TORRENT_DIR`: Directory for storing `.torrent` files uploaded by users.
- `PEER_FILE`: File for storing peer information for each torrent.
- `TORRENT_FILE`: File for storing metadata about torrents.

### Peer Configuration
- `TRACKER_URL`: URL of the tracker.
- `TORRENT_DIR`: Directory for storing created `.torrent` files.
- `DOWNLOAD_DIR`: Directory for storing downloaded files.
- `INTERVAL`: Interval (in seconds) for sending announcements to the tracker.
- `PORT`: Default port for the torrent daemon.
---


## Usage

### 1. Start the Tracker
Run the tracker server to handle torrent announcements and peer management:
```bash
torrent-tracker --help                        # Display usage guide
torrent-tracker                               # Start tracker on default host (127.0.0.1) and port (8000)
torrent-tracker --host 0.0.0.0 --port 8080    # Start tracker on a specific host and port
```

### 2. Start the Torrent Daemon (for peers)
The `torrent-daemon` handles seeding and leeching operations on the client side:
```bash
torrent-daemon --help        # Display usage guide
torrent-daemon               # Start daemon on default port (5000)
torrent-daemon --port <port> # Start daemon on a specific port
```

### 3. Torrent CLI Commands
Use the following commands to interact with the `torrent-daemon`:

#### Check Daemon Status
Verify if the torrent daemon is running:
```bash
torrent-test --port <port>
```

#### Seed a File
Start seeding a file:
```bash
torrent-seed --input <filepath> --private --piece-length <length>
```
- `--input`: Path to the file or directory to seed.
- `--private`: Flag to prevent public sharing of the torrent file.
- `--piece-length`: Specify the piece length (optional).

#### Fetch Torrents
Fetch available torrents from the tracker:
```bash
torrent-fetch --port <port>
```

#### Leech a File
Download a file using a `.torrent` file:
```bash
torrent-leech --torrent <filepath>
```
- `--torrent`: Path to the `.torrent` file.

#### Check Status
View the status of seeding and leeching operations:
```bash
torrent-status --port <port>
```
---
## Example Workflow

1. Start the tracker (on server machine):
   ```bash
   torrent-tracker
   ```

2. Start the torrent daemon (on client machines):
   ```bash
   torrent-daemon
   ```

3. Seed a file for other peers to download:
   ```bash
   torrent-seed --input /path/to/file
   ```

4. Fetch available files to download:
   ```bash
   torrent-fetch
   ```

5. Download a file from other peers:
   ```bash
   torrent-leech --torrent /path/to/torrent/file
   ```

6. Check the status of operations:
   ```bash
   torrent-status
   ```

---
