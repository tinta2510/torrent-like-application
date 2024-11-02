import socket

def download_file(filename, host='localhost', port=6881, piece_size=16384):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print("Connected to the server.")

    with open(filename, 'wb') as f:
        while True:
            # Receive data in chunks of piece_size
            data = client_socket.recv(piece_size)
            
            # Break if no more data is received
            if not data:
                break

            # Write received data to file
            f.write(data)
            print(f"Received piece of size: {len(data)} bytes")

    print("File download completed.")
    client_socket.close()

# Usage
download_file("downloaded_file")

# dung truncate để set file size