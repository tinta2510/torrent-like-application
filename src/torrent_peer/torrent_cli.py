import click
import requests
from tabulate import tabulate
from InquirerPy import inquirer

@click.command()
@click.option('--port', type=int, required=True, help="Choost port number of torrent daemon")
@click.option('--input-path', 
              type=click.Path(exists=True, file_okay=True, dir_okay=True),
              help="Path to file that needs seeding.",
              required=True)
@click.option('--trackers', default=None, help="List of list of tracker URL(comma-separated)")
@click.option('--public', default=None, help="Public the torrent file or not")
@click.option('--piece-length', default=None, type=int, help="Piece length for the torrent file.")
@click.option('--torrent-filepath', default=None, help="Path to save the generated torrent file.")
@click.option('--name', default=None, help="Name of the torrent.")
@click.option('--description', default=None, help="Description of the torrent.")
def seed(port, input_path, trackers, public, piece_length, torrent_filepath, name, description):
    url = f"http://localhost:{port}/seed"

    payload = { "input_path": input_path }
    if trackers: payload["trackers"] = [[t.strip() for t in trackers.split(',')]]
    if public: payload["public"] = public
    if piece_length: payload["piece_length"] = piece_length
    if torrent_filepath: payload["torrent_filepath"] = torrent_filepath
    if name: payload["name"] = name
    if description: payload["description"] = description

    try:
        response = requests.post(url, json=payload, timeout=3)
        response.raise_for_status()
        click.echo(f"{response.json()["message"]}")
    except requests.exceptions.ConnectionError as e:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.") 
    except requests.exceptions.Timeout as http_err:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.") 
    except Exception as err:
        click.echo(f"An error occurred: {err}")

@click.command()
@click.option('--port', type=int, required=True, help="Choost port number of torrent daemon")
def get_torrent(port):
    url = f"http://localhost:{port}/torrents"
    try:
        # Send a GET request
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP errors

        # Parse and print the response
        data: dict = response.json()['data']
        rows = [[key, value["name"], value["description"]] for key, value in data.items()]
        click.echo(tabulate(rows, headers=["info_hash", "Name", "Description"], tablefmt="grid"))
    
        info_hash = inquirer.select(
            message="Select a torrent file to download:",
            choices= data.keys(),
            default=list(data.keys())[0],
        ).execute()

        click.echo(f"Selected file: {info_hash}")

        response = requests.get(url + "/" + info_hash)
        response.raise_for_status()
        click.echo(f"Download torrent file {info_hash} successfully.")
    except requests.exceptions.ConnectionError as e:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.")
    except requests.exceptions.Timeout as http_err:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.") 
    except Exception as err:
        click.echo(f"An error occurred: {err}")

@click.command()
@click.option('--port', type=int, required=True, help="Port number of the torrent server.")
@click.option(
    '--torrent-filepath',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="Path to the torrent file that needs leeching."
)
def leech(port, torrent_filepath):
    url = f"http://localhost:{port}/leech"
    payload = {"torrent_filepath": torrent_filepath}
    try:
        response = requests.post(url, json=payload, timeout=3)
        response.raise_for_status()
        click.echo(f"{response.json()["message"]}")
    except requests.exceptions.ConnectionError as e:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.") 
    except requests.exceptions.Timeout as http_err:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.") 
    except Exception as err:
        click.echo(f"An error occurred: {err}")

@click.command()
@click.option('--port', type=int, required=True, help="Port number of the torrent server.")
def status(port):
    url = f"http://localhost:{port}/status"
    try:
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
        
    except requests.exceptions.ConnectionError as e:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.")
    except requests.exceptions.Timeout as http_err:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.") 
    except Exception as err:
        click.echo(f"An error occurred: {err}")

@click.command()
@click.option('--port', type=int, required=True, help="Port number of the torrent server.")
def test(port):
    url = f"http://localhost:{port}"

    try:
        # Send a GET request
        print("Send requests")
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP errors
        click.echo(response.json())
    except requests.exceptions.ConnectionError as e:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.")
    except requests.exceptions.Timeout as http_err:
        click.echo(f"[ERROR] Run torrent_daemon and verify port number.") 
    except Exception as err:
        click.echo(f"An error occurred: {err}")
