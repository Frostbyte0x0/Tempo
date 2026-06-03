import json
import logging
import socket
import sys

# Configure logging to save to a file
# noinspection PyArgumentList
logging.basicConfig(
    encoding='utf-8',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("server.log", mode="w"),
        logging.StreamHandler(sys.stdout)
    ],
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# TODO:
# - Implement server logic to receive data from clients and sync it
# -
# -
# -
# - Website to show the data nicely


def wait_and_manage_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 8080))
    s.listen(5)

    try:
        while True:
            c, addr = s.accept()
            received = c.recv(1024)

            if received:
                data = json.loads(received.decode("utf-8"))
                device_name = data["device_name"]
                logging.info(f"Received data from {device_name}")

            c.close()
    finally:
        s.close()


if __name__ == "__main__":
    wait_and_manage_connection()
