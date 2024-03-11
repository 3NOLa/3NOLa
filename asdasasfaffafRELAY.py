import socket
from threading import Thread
import threading
import queue

def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf

def thread_function_2(host, port, communication_queue, communication_queue2):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind((host, port))

    try:
        client_socket.listen(1)
        print('Server started.')
        client_socket2, addr = client_socket.accept()
        print('Client connected IP:', addr)
        while True:
            message = communication_queue.get()
            size = len(message)
            size_len = (size.bit_length() + 7) // 8
            client_socket2.send(b"S" + bytes([size_len]))
            size_bytes = size.to_bytes(size_len, 'big')
            client_socket2.send(size_bytes)
            client_socket2.sendall(message)
            if not communication_queue2.empty():
                message = communication_queue2.get()
                size = len(message)
                size_len = (size.bit_length() + 7) // 8
                client_socket2.send(b"K" + bytes([size_len]))
                size_bytes = size.to_bytes(size_len, 'big')
                client_socket2.send(size_bytes)
                client_socket2.sendall(message)


    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()


def start_server(host, port, communication_queue, communication_queue2):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))

    try:
        server_socket.listen(1)
        print('Server started.')
        server_socket2, addr = server_socket.accept()
        print('Client connected IP:', addr)

        while True:
            perfix = server_socket2.recv(1)
            size_len = int.from_bytes(server_socket2.recv(1), byteorder='big')
            size = int.from_bytes(server_socket2.recv(size_len), byteorder='big')
            data = recvall(server_socket2, size)
            if perfix == b"S":
                communication_queue.put(data)
            elif perfix == b"K":
                communication_queue2.put(data)

    except Exception as e:
        print("Error:", e)

    finally:
        # Close the server socket in case of an exception
        server_socket2.close()
        server_socket.close()




if __name__ == "__main__":
    communication_queue = queue.Queue()
    communication_queue2 = queue.Queue()
    thread1 = threading.Thread(target=start_server, args=("0.0.0.0", 5000, communication_queue, communication_queue2,))
    thread2 = threading.Thread(target=thread_function_2, args=("0.0.0.0", 5001, communication_queue, communication_queue2,))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
