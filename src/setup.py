from setuptools import setup, find_packages

setup(
    name="torrent-tool",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "aiofiles",
        "bencodepy",
        "bitstring",
        "click",
        "InquirerPy",
        "quart",
        "requests",  
        "tabulate",
        "tqdm",
        "fastapi",
        "uvicorn",
    ],
    entry_points={
        "console_scripts": [
            "torrent-daemon=torrent_peer.daemon:main",
            "torrent-tracker=torrent_tracker.tracker:main",
            "torrent-seed=torrent_peer.torrent_cli:seed",
            "torrent-fetch=torrent_peer.torrent_cli:get_torrent",
            "torrent-leech=torrent_peer.torrent_cli:leech",
            "torrent-status=torrent_peer.torrent_cli:status",
            "torrent-test=torrent_peer.torrent_cli:test"
        ],
    },
)