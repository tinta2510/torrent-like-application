import socket
import os

def send_file_piece(filename, piece_index, piece_size, conn):
    with open(filename, 'rb') as f:
        f.seek(piece_index * piece_size)
        data = f.read(piece_size)
        conn.sendall(data)

def upload_file(filename, piece_size=16384):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 6881))
    server_socket.listen(5)
    print("Uploader is ready and listening for connections.")

    while True:
        conn, addr = server_socket.accept()
        print(f"Connected to peer: {addr}")

        file_size = os.path.getsize(filename)
        num_pieces = (file_size + piece_size - 1) // piece_size

        for piece_index in range(num_pieces):
            send_file_piece(filename, piece_index, piece_size, conn)
            print(f"Sent piece {piece_index + 1}/{num_pieces}")

        conn.close()
        print("File upload completed for this peer.")

# Usage
upload_file("path_to_your_file")
