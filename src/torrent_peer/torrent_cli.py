import click
import requests
from tabulate import tabulate
from InquirerPy import inquirer
import time
import logging
from torrent_peer.config_loader import PORT, TRACKER_URL

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def handle_exceptions(func):
    """
    A decorator to handle exceptions for HTTP requests.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            logging.error("Cannot connect to torrent-daemon.")
            print("     Try running torrent-daemon and choosing the correct port number (using --port).")
        except requests.exceptions.Timeout:
            logging.error("The request timed out. Verify torrent-daemon is running and try again.")
        except requests.exceptions.HTTPError as http_err:
            # Catch HTTP errors
            logging.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            # Catch non-HTTP errors like connection problems
            print(f"Other request error occurred: {req_err}")
        except Exception as err:
            logging.error(f"An error occurred: {err}")
    return wrapper

@click.command()
@click.option('--port', type=int, default=PORT, help="Choost port number of torrent daemon")
@click.option('--input', 
              'input_path',
              type=click.Path(exists=True, file_okay=True, dir_okay=True),
              help="Path to file that needs seeding.",
              required=True)
@click.option('--trackers', default=None, help="List of list of tracker URL(comma-separated)")
@click.option('--private', is_flag=True, help="Don't public the torrent file for everyone to download")
@click.option('--piece-length', default=None, type=int, help="Piece length for the torrent file.")
@click.option('--torrent', 
              'torrent_filepath',
              default=None, 
              help="Path to save the generated torrent file.")
@click.option('--name', default=None, help="Name of the torrent.")
@click.option('--description', default=None, help="Description of the torrent.")
@handle_exceptions
def seed(port, input_path, trackers, private, piece_length, torrent_filepath, name, description):
    url = f"http://127.0.0.1:{port}/seed"

    payload = { "input_path": input_path }
    if trackers: payload["trackers"] = [[t.strip() for t in trackers.split(',')]]
    if private: payload["public"] = False
    if piece_length: payload["piece_length"] = piece_length
    if torrent_filepath: payload["torrent_filepath"] = torrent_filepath
    if name: payload["name"] = name
    if description: payload["description"] = description

    response = requests.post(url, json=payload, timeout=3)
    response.raise_for_status()
    logging.info(f"{response.json()['message']}")

@click.command()
@click.option('--port', type=int, default=PORT, help="Choost port number of torrent daemon")
@handle_exceptions
def get_torrent(port):
    url = f"http://127.0.0.1:{port}/torrents"
    # Send a GET request
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for HTTP errors

    # Parse and print the response
    data: dict = response.json()['data']
    rows = [[key, value["name"], value["description"]] for key, value in data.items()]
    click.echo(tabulate(rows, headers=["info_hash", "Name", "Description"], tablefmt="grid"))

    choices = [(key[:5]+' - '+value["name"], key) for key, value in data.items()]
    selected_file = inquirer.select(
        message="Select a torrent file to download:",
        choices= [choice[0] for choice in choices],
        default= choices[0][0],
    ).execute()

    info_hash = next(key for label, key in choices if label == selected_file)

    logging.info(f"Selected file: {info_hash}")

    response = requests.get(url + "/" + info_hash)
    data = response.json()["data"]
    response.raise_for_status()
    logging.info(f"Download torrent file {info_hash} successfully.\nFilepath: {data}")

@click.command()
@click.option('--port', type=int, default=PORT, help="Port number of the torrent server.")
@click.option(
    '--torrent',
    'torrent_filepath',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="Path to the torrent file that needs leeching."
)
@handle_exceptions
def leech(port, torrent_filepath):
    url = f"http://127.0.0.1:{port}/leech"
    payload = {"torrent_filepath": torrent_filepath}
    response = requests.post(url, json=payload, timeout=3)
    response.raise_for_status()
    click.echo(f"{response.json()['message']} ...")
    click.echo(f"Go to the torrent-daemon terminal to see details.")
@click.command()
@click.option('--port', type=int, default=PORT, help="Port number of the torrent server.")
@handle_exceptions
def status(port):
    url = f"http://127.0.0.1:{port}/status"
    # Send a GET request
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for HTTP errors
    data = response.json()

    seeding_data: list = data['seeding']
    click.echo("SEEDING FILES:")
    click.echo(tabulate(
        seeding_data, 
        headers=["info_hash", "filepath"],
        tablefmt="grid")
    )

    leeching_data: list = data["leeching"]
    click.echo("LEECHING FILES:")
    click.echo(tabulate(
        leeching_data,
        headers=["info_hash", "filepath", "status"],
        tablefmt="grid"
    ))


@click.command()
@click.option('--port', type=int, default=PORT, help="Port number of the torrent server.")
@handle_exceptions
def test(port):
    """
    Tests a connection to the given port by sending a GET request.
    """
    url = f"http://127.0.0.1:{port}"
    # Send a GET request
    start = time.time()
    response = requests.get(url, verify=False)
    response.raise_for_status()  # Raise an error for HTTP errors
    click.echo(response.json())

    tracker_url = TRACKER_URL
    response = requests.get(tracker_url, verify=False)
    response.raise_for_status()
    click.echo(response.json())

    print(time.time() - start)
