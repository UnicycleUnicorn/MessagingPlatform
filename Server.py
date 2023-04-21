import NetworkHandler
import Packet
from typing import Tuple

class Server:
    def __init__(self, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__)

    def send(self, message: str, recipient: Tuple[str, int]):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, 69420)
        self.handler.send_message(message, recipient)

    def ack(self, mesid: bytes, recipient: Tuple[str, int]):
        message = Packet.Message(b'', Packet.PayloadType.ACKNOWLEDGE, 69420, messageid=mesid)
        self.handler.send_message(message, recipient)

    def __recv__(self, message: Packet.Message):
        self.ack(message.messageid, message.sender)
