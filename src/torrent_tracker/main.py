import uvicorn
import click

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
              default=8080,
              help="The binding port. (default: 8080)")
def main(host, port):
    """
    Start the tracker.
    """
    uvicorn.run(f"torrent_tracker.tracker:app", 
                host=host,
                port=port,
                reload=False)

if __name__ == "__main__":
    main()