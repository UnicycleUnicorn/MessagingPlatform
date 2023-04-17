import socket
import Packet
from typing import Callable, Tuple
import threading
import logging


class NetworkHandler:
    def __init__(self, port: int, host: str = ''):
        self.PORT = port
        self.HOST = host
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SOCKET.bind(('', self.PORT))
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.LISTENERS: list[Callable[[Tuple[str, int], Packet.Packet], None]] = []
        threading.Thread(target=self.__listen__).start()

    def __listen__(self):
        while True:
            sender = None
            raw_header = self.SOCKET.recv(Packet.HeaderFormat.LENGTH)
            if not raw_header:
                break
            header = Packet.Header.from_bytes(raw_header)
            raw_message = b''
            while len(raw_message) < header.messagelength:
                raw_mes_new, sender = self.SOCKET.recvfrom(header.messagelength - len(raw_message))
                raw_message += raw_mes_new
            threading.Thread(target=self.__received_message__, args=(header, raw_message, sender)).start()

    def __received_message__(self, header: Packet.Header, raw_message: bytes, sender: Tuple[str, int]):
        packet = Packet.Packet(header, Packet.Payload.from_bytes(raw_message))
        for listener in self.LISTENERS:
            listener(sender, packet)

    def add_listener(self, listener: Callable[[Tuple[str, int], Packet.Packet], None]):
        self.LISTENERS.append(listener)

    def send_packet(self, packet: Packet.Packet, recipient=None) -> bool:
        if recipient is None:
            recipient = (self.HOST, self.PORT)
        try:
            self.SOCKET.sendto(packet.to_bytes(), recipient)
            return True
        except socket.error as e:
            logging.info(f"Failed to send packet: {e}")
            return False

    def send_message(self, message: Packet.Message, recipient=None) -> bool:
        if recipient is None:
            recipient = (self.HOST, self.PORT)
        try:
            for packetbytes in message.to_bytes_list():
                self.SOCKET.sendto(packetbytes, recipient)
            return True
        except socket.error as e:
            logging.info(f"Failed to send message: {e}")
            return False