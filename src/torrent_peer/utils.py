import socket

def get_local_ip():
    # Get the hostname
    hostname = socket.gethostname()
    # Get the local IP address
    local_ip = socket.gethostbyname(hostname)
    return local_ip