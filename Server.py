import logging
import socket
import threading
import Packet


class Server:
    def __init__(self, port: int):
        self.host = socket.gethostbyname(socket.gethostname())
        logging.info(f"IP: {self.host}")
        self.port = port
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
            logging.info(packet.__str__())
            self.clientSocket.sendall(packet.to_bytes())
        else:
            logging.info('No client connection')

    def __awaitmessage__(self):
        while True:
            rawhead = self.clientSocket.recv(Packet.HeaderFormat.TOTAL_LENGTH)
            if not rawhead:
                break
            head = Packet.PacketHeader.from_bytes(rawhead)
            logging.info(head.messagelength)
            rawmessage = b''
            while len(rawmessage) < head.messagelength:
                logging.warning("CHECKED")
                newmessage = self.clientSocket.recv(head.messagelength - len(rawmessage))
                rawmessage += newmessage

            messagepacket = Packet.PacketMessage.from_bytes(rawmessage)
            packet = Packet.Packet(head, messagepacket)
            logging.info(packet.__str__())
            messagetext = messagepacket.message
            threading.Thread(target=self.__received__, args=(messagetext,)).start()

    def __received__(self, message: str):
        #logging.info(message)
        logging.info("RECEIVED")

    def close(self):
        if self.clientSocket:
            self.clientSocket.close()
            self.clientSocket = None
        if self.serverSocket:
            self.serverSocket.close()
            self.serverSocket = None

    def __del__(self):
        self.close()
