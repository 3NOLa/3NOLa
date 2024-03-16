import socket
from threading import Thread
import threading
import queue
import select

def protocol_encode(message, perfix, client_socket):
    size = len(message)
    size_len = (size.bit_length() + 7) // 8
    client_socket.send(perfix + bytes([size_len]))
    size_bytes = size.to_bytes(size_len, 'big')
    client_socket.send(size_bytes)
    client_socket.sendall(message)


def protocol_decode(client_socket, communication_queue, communication_queue2):
    perfix = client_socket.recv(1)
    size_len = int.from_bytes(client_socket.recv(1), byteorder='big')
    size = int.from_bytes(client_socket.recv(size_len), byteorder='big')
    data = recvall(client_socket, size)
    if perfix == b"S":
        communication_queue.put(data)
    elif perfix == b"K":
        communication_queue2.put(data)


def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf


def thread_function_2(host, port, communication_queue, communication_queue2, reverse_queue, reverse_queue2):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind((host, port))

    try:
        client_socket.listen(1)
        print('Server started.')
        client_socket2, addr = client_socket.accept()
        sockets_to_check = [client_socket2]
        print('Client connected IP:', addr)
        while True:
            message = communication_queue.get()
            protocol_encode(message, b"S", client_socket2)
            if not communication_queue2.empty():
                message = communication_queue2.get()
                protocol_encode(message, b"K", client_socket2)
            readable, _, _ = select.select(sockets_to_check, [], [], 0)
            if client_socket2 in readable:
                protocol_decode(client_socket2, reverse_queue, reverse_queue2)


    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()


def start_server(host, port, communication_queue, communication_queue2, reverse_queue, reverse_queue2):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))

    try:
        server_socket.listen(1)
        print('Server started.')
        server_socket2, addr = server_socket.accept()
        print('Client connected IP:', addr)

        while True:
            protocol_decode(server_socket2, communication_queue, communication_queue2)
            if not reverse_queue.empty():
                message = reverse_queue.get()
                protocol_encode(message, b"S", server_socket2)
            elif not reverse_queue2.empty():
                message = reverse_queue2.get()
                protocol_encode(message, b"K", server_socket2)


    except Exception as e:
        print("Error:", e)

    finally:
        server_socket.close()


if __name__ == "__main__":
    communication_queue = queue.Queue()
    communication_queue2 = queue.Queue()
    reverse_queue = queue.Queue()
    reverse_queue2 = queue.Queue()
    thread1 = threading.Thread(target=start_server, args=(
    "0.0.0.0", 5000, communication_queue, communication_queue2, reverse_queue, reverse_queue2,))
    thread2 = threading.Thread(target=thread_function_2, args=(
    "0.0.0.0", 5001, communication_queue, communication_queue2, reverse_queue, reverse_queue2,))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
