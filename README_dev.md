# The workflow of tracker and peers
*Reference:* http://bittorrent.org/beps/bep_0003.html

## Tracker HTTP protocol
- Peers send request to tracker.
  - Started request
  - Stopped request: send to the tracker if the client is shutting down,
  - Completed request: when the download completes.
- Tracker response.

## Peer - Downloading 
1. Connect to tracker to get the list of peers.
2. Connect to as many of peers as possible (using TCP + 2-way handshake)
3. Start downloading
4. Send response when you finish downloading a piece.

## Peer - Uploading
1. Have the tracker started already (run our own tracker / use a public tracker) and make the tracker be ready to receive .torrent file.
2. Generate a metainfo (.torrent) file using the complete file to be served and the URL of the tracker.
3. Send the metainfo file to the tracker.


### Load config file
```python
import json

# Load JSON configuration from file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

tracker_config = config['tracker']
```