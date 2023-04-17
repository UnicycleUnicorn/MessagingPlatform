import socket
import threading
import logging
import Packet


class Client:
    def __init__(self, port: int, serverip: str):
        self.host = serverip
        self.port = port
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clientSocket.connect((self.host, self.port))
        logging.info("Connected to server")
        threading.Thread(target=self.__awaitmessage__).start()

    def send(self, message: str):
        if self.clientSocket:
            packet = Packet.Packet.construct(message)
            logging.info(packet.__str__())
            self.clientSocket.sendall(packet.to_bytes())
        else:
            logging.info('No server connection')

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

    def __del__(self):
        self.close()
