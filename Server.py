from typing import Tuple

import NetworkHandler
import Packet


class Server:
    def __init__(self, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__)

    def send(self, message: str, recipient: Tuple[str, int]):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, 69420)
        self.handler.send_message(message, recipient)

    def __recv__(self, message: Packet.Message):
        pass
