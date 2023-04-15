import socket
import threading
import logging
import Packet


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
            packet = Packet.Packet.construct(message)
            self.clientSocket.sendall(packet.tobytes())
        else:
            logging.info('No server connection')

    def __awaitmessage__(self):
        while True:
            rawhead = self.clientSocket.recv(Packet.HeaderFormat.TOTAL_LENGTH)
            if not rawhead:
                break
            head = Packet.PacketHeader.frombytes(rawhead)
            rawmessage = self.clientSocket.recv(head.messagelength)
            message = Packet.PacketMessage.frombytes(rawmessage).message
            threading.Thread(target=self.__received__, args=(message, )).start()

    def __received__(self, message: str):
        logging.info(message)

    def close(self):
        if self.clientSocket:
            self.clientSocket.close()
            self.clientSocket = None

    def __del__(self):
        self.close()
