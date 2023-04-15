import socket
import threading
import logging


class Client:
    def __init__(self, serverip: str):
        self.host = serverip
        self.port = 8888
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clientSocket.connect((self.host, self.port))
        logging.info("Connected to server")
        threading.Thread(target=self.__awaitmessage__).start()

    def send(self, message: str):
        if self.clientSocket:
            encoded = message.encode()
            self.clientSocket.send(encoded)
        else:
            logging.info('No server connection')

    def __awaitmessage__(self):
        while True:
            data = self.clientSocket.recv(1024)
            if not data:
                break
            threading.Thread(target=self.__received__, args=(data, )).start()

    def __received__(self, message: bytes):
        try:
            logging.info(message.decode())
        except:
            logging.info(f"Received non-decodable message: {message}")

    def close(self):
        if self.clientSocket:
            self.clientSocket.close()
            self.clientSocket = None

    def __del__(self):
        self.close()
