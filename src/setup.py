from setuptools import setup, find_packages

setup(
    name="torrent-tool",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "uvicorn",  # Ensure uvicorn is installed with the package
    ],
    entry_points={
        "console_scripts": [
            "torrent-daemon=torrent_peer.daemon:main",
            "torrent-tracker=torrent_tracker.main:main",
            "torrent-seed=torrent_peer.torrent_cli:seed",
            "torrent-fetch=torrent_peer.torrent_cli:get_torrent",
            "torrent-leech=torrent_peer.torrent_cli:leech",
            "torrent-status=torrent_peer.torrent_cli:status"
        ],
    },
)