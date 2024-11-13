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
            "torrent_peer=torrent_peer.main:main",
            "torrent_tracker=torrent_tracker.main:main"
        ],
    },
)