import logging
import socket
import multiprocessing


class Server:
    def __init__(self):
        self.host = socket.gethostbyname(socket.gethostname())
        logging.info(f"IP: {self.host}")
        self.port = 8888
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.host, self.port))
        self.serverSocket.listen(1)
        logging.info('Waiting for a client to connect...')
        # Accept a client connection
        self.clientSocket, self.clientAddress = self.serverSocket.accept()
        logging.info(f'Client connected from: {self.clientAddress}')
        multiprocessing.Process(target=self.__awaitmessage__).start()

    def send(self, message: str):
        if self.clientSocket:
            encoded = message.encode()
            self.clientSocket.send(encoded)
        else:
            logging.info('No client connection')

    def __awaitmessage__(self):
        while True:
            data = self.clientSocket.recv(1024)
            if not data:
                break
            multiprocessing.Process(target=self.__received__, args=(data, )).start()

    def __received__(self, message: bytes):
        try:
            logging.info(message.decode())
        except:
            logging.info(f"Received non-decodable message: {message}")

    def close(self):
        if self.clientSocket:
            self.clientSocket.close()
            self.clientSocket = None
        if self.serverSocket:
            self.serverSocket.close()
            self.serverSocket = None

    def __del__(self):
        self.close()
