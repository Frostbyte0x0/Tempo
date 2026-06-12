import json
import logging
import socket
import struct
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

def read_project_list() -> dict:
    with open("project_list.json", "r") as f:
        return json.load(f)

def write_project_list(project_list: dict):
    with open("project_list.json", "w") as f:
        json.dump(project_list, f, indent=2)

def read_data() -> dict:
    with open("data.json", "r") as f:
        return json.load(f)

def write_data(data: dict):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)


def wait_and_manage_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 8080))
    s.listen(5)
    logging.info("Server started, waiting for connections on localhost:8080...")

    try:
        while True:
            c, addr = s.accept()
            logging.info(f"Connection established from {addr}")

            is_project_list = struct.unpack('?', c.recv(1))[0]

            received = c.recv(1024)

            if received:
                new_data = json.loads(received.decode("utf-8"))
                device_name = new_data["device_name"]
                logging.info(f"Received data from {device_name}")
                new_data.pop("device_name")

                if is_project_list:
                    project_list = read_project_list()
                    project_list[device_name] = new_data
                    write_project_list(project_list)
                    logging.info(f"Wrote project list to {device_name}")

                else:
                    data = read_data()
                    data[device_name] = new_data
                    write_data(data)
                    logging.info(f"Wrote data to {device_name}")

            c.close()
    finally:
        s.close()


if __name__ == "__main__":
    try:
        wait_and_manage_connection()
    except Exception as e:
        logging.error(e, exc_info=True)
