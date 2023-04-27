import NetworkHandler
import Packet


class Client:
    def __init__(self, serverip: str, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__, host=serverip)

    def send(self, message: str):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, 69420)
        self.handler.send_message(message, None)

    def __recv__(self, message: Packet.Message):
        pass
