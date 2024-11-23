# Torrent-like application
## Overview
This project implements a simple BitTorrent-like P2P file-sharing system (clients and tracker). 

## Features
### Tracker

### Peer
- **Torrent File Creation and Parsing:** Generate a `.torrent` file for a single file or a directory and read infomation in a `.torrent` file. 

## Usage
1. **Clone the Repository**
```bash
git clone https://github.com/tinta2510/torrent-like-application.git
```

2. **Install the package**
Install the package and required dependencies:
```bash
cd torrent-like-application/src 
pip install .
```

3. **Configure the application (optional)**
Edit the `config.ini` if needed:
- `[tracker]`: 
  - `TORRENT_DIR`: Directory for storing `.torrent` files from users. 
  - `PEER_FILE`: Files for storing peer swarms corresponding to torrents.
  - `TORRENT_FILE`: Files for storing metadata for stored torrent files in the tracker database.
- `[peer]`: 
  - `TRACKER_URL`: The URL of the tracker.
  - `TORRENT_DIR`: Directory for storing create torrent files.
  - `DOWNLOAD_DIR`: Directory for storing downloaded files.
  - `INTERVEL`: Interval for sending announces to trackers (second).

4. **Start the tracker**
Run the tracker server, which will handle torrent announcements and peer management:
```bash
torrent-tracker --help                        # for usage guide
torrent-tracker                               # Running on default host: 127.0.0.1, port: 8080
torrent-tracker --host 0.0.0.0 --port 8080
```

5. **Run torrent-daemon**
- The `torrent-daemon` is the process for seeding and leeching torrents on the client side.
```bash
torrent-daemon --help        # for user's guide
torrent-daemon               # Running on default port 5000
torrent-deamon --port <port> # Running torrent-daemon on specific port 
```

6. **Torrent CLI**
- To send command to the `torrent-daemon`. 