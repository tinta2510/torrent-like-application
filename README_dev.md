# The workflow of tracker and peers
*Reference:* http://bittorrent.org/beps/bep_0003.html
## Peers
### When a peer want to serve a file
1. Have the tracker started already (run our own tracker / use a public tracker) and make the tracker be ready to receive .torrent file.
2. Generate a metainfo (.torrent) file using the complete file to be served and the URL of the tracker.
3. Send the metainfo file to the tracker.

- Things to do for this part:
  - Create a torrent file. Aims:
    - Can create a torrent file for multiple served files (a directory).


## Components
- Tracker - Clients
- Peer - to - peer

## Load config file
```python
import json

# Load JSON configuration from file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

tracker_config = config['tracker']
```