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
            "torrent_daemon=torrent_peer.daemon:main",
            "torrent_tracker=torrent_tracker.main:main",
            "torrent_seed=torrent_peer.torrent_cli:seed",
            "torrent_fetch=torrent_peer.torrent_cli:get_torrent",
            "torrent_leech=torrent_peer.torrent_cli:leech"
        ],
    },
)