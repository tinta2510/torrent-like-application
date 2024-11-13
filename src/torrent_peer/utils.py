import socket
import os
def get_local_ip():
    """ Function to get local ip of the current machine """
    # Get the hostname
    hostname = socket.gethostname()
    # Get the local IP address
    local_ip = socket.gethostbyname(hostname)
    return local_ip

def get_unique_filename(file_path):
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename

    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}_{counter}{ext}"
        counter += 1

    return os.path.join(directory, unique_filename)
