import socket
import Packet
from typing import Callable, Tuple
import threading
import MessageReconstructor

import logwrapper


class NetworkHandler:
    def __init__(self, port: int, listener: Callable[[Packet.Message], None], host: str = ''):
        self.MESSAGE_RECONSTRUCTOR = MessageReconstructor.MessageReconstructor()
        self.RECONSTRUCTOR_LOCK = threading.Lock()
        self.PORT = port
        self.HOST = host
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SOCKET.bind(('', self.PORT))
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8192)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)
        self.MESSAGE_LISTENER = listener
        t = threading.Thread(target=self.__listen__)
        t.daemon = True
        t.start()

    def __listen__(self):
        while True:
            raw_packet, sender = self.SOCKET.recvfrom(Packet.Packet.MAX_PACKET_SIZE)
            if not raw_packet:
                break
            t = threading.Thread(target=self.__received_packet__, args=(raw_packet, sender))
            t.daemon = True
            t.start()

    def __received_packet__(self, raw_packet: bytes, sender: Tuple[str, int]):
        packet = Packet.Packet.from_bytes(raw_packet)
        logwrapper.received_packet(packet)
        message: Packet.Message | None
        with self.RECONSTRUCTOR_LOCK:
            message = self.MESSAGE_RECONSTRUCTOR.received_packet(packet, sender)
        if message is not None:
            logwrapper.received_message(message)
            self.MESSAGE_LISTENER(message)

    def __send_packet__(self, packet: Packet.Packet, recipient=None) -> bool:
        if recipient is None:
            recipient = (self.HOST, self.PORT)
        try:
            self.SOCKET.sendto(packet.to_bytes(), recipient)
            logwrapper.sent_packet(packet)
            return True
        except socket.error as e:
            logwrapper.failed_to_send_packet(packet, e)
            return False

    def send_message(self, message: Packet.Message, recipient=None):
        for packet in message.to_packet_list():
            if not self.__send_packet__(packet, recipient):
                logwrapper.failed_to_send_message(message)
                return False
        logwrapper.sent_message(message)
        return True
