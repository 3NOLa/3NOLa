import socket
from threading import Thread
from zlib import compress
from mss import mss
from pynput import keyboard
import select
from pynput.keyboard import Controller, Key

WIDTH = 1900
HEIGHT = 1000
conn = None  # Global connection variable


def protocol_encode(message, perfix):
    global conn
    client_socket = conn
    size = len(message)
    size_len = (size.bit_length() + 7) // 8
    client_socket.send(perfix + bytes([size_len]))
    size_bytes = size.to_bytes(size_len, 'big')
    client_socket.send(size_bytes)
    if perfix != b"S":
        client_socket.sendall(message.encode())
    else:
        client_socket.sendall(message)

def protocol_decode():
    global conn
    client_socket = conn
    perfix = client_socket.recv(1)
    size_len = int.from_bytes(client_socket.recv(1), byteorder='big')
    size = int.from_bytes(client_socket.recv(size_len), byteorder='big')
    data = client_socket.recv(size)
    if perfix == b"K":
        press_key(data)

def retrieve_screenshot():
    global conn
    sockets_to_check = [conn]
    with mss() as sct:
        rect = {'top': 0, 'left': 0, 'width': WIDTH, 'height': HEIGHT}
        try:
            while True:
                img = sct.grab(rect)
                pixels = compress(img.rgb, 6)
                protocol_encode(pixels, b"S")
                readable, _, _ = select.select(sockets_to_check, [], [], 0)
                if conn in readable:
                    protocol_decode()
        except Exception as e:
            print(f"Error in retrieve_screenshot: {e}")


def press_key(key):
    keyboard = Controller()

    # If the key is a byte string, convert it to a string
    if isinstance(key, bytes):
        key = key.decode('utf-8')
    # Press the key
    keyboard.press(key)

def start_keyboard_listener():
    with keyboard.Listener(on_press=on_key_press) as keyboard_listener:
        keyboard_listener.join()

def on_key_press(key):
    try:
        key_char = key.char
    except AttributeError:
        # Handle special keys
        key_char = str(key)
        if key == key.space:
            key_char = " "
    protocol_encode(key_char, b"K")

def main(host='127.0.0.1', port=5000):
    global conn
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    try:
        conn = sock
        screenshot_thread = Thread(target=retrieve_screenshot)
        keyboard_thread = Thread(target=start_keyboard_listener)

        screenshot_thread.start()
        keyboard_thread.start()

        keyboard_thread.join(timeout=30)
        screenshot_thread.join()


    finally:
        sock.close()

if __name__ == '__main__':
    main()