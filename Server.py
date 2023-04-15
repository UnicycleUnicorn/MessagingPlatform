import logging
import socket
import threading
import Packet


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
        threading.Thread(target=self.__awaitmessage__).start()

    def send(self, message: str):
        if self.clientSocket:
            packet = Packet.Packet.construct(message)
            self.clientSocket.send(packet.tobytes())
        else:
            logging.info('No client connection')

    def __awaitmessage__(self):
        while True:
            rawhead = self.clientSocket.recv(Packet.HeaderFormat.TOTAL_LENGTH)
            if not rawhead:
                break
            head = Packet.PacketHeader.frombytes(rawhead)
            rawmessage = self.clientSocket.recv(head.messagelength)
            message = Packet.PacketMessage.frombytes(rawmessage)
            threading.Thread(target=self.__received__, args=(message,)).start()

    def __received__(self, message: str):
        logging.info(message)

    def close(self):
        if self.clientSocket:
            self.clientSocket.close()
            self.clientSocket = None
        if self.serverSocket:
            self.serverSocket.close()
            self.serverSocket = None

    def __del__(self):
        self.close()
