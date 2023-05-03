import NetworkHandler
import Packet
from typing import Tuple
import BetterLog


class Client:
    def __init__(self, serverip: str, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__, host=serverip)

        self.handler.send_message(Packet.Message(b'', Packet.PayloadType.CONNECT, 69420), None)

    def send(self, message: str):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, 69420)
        self.handler.send_message(message, None)

    def __recv__(self, message: Packet.Message):
        messageid: bytes = message.messageid
        sender: Tuple[str, int] = message.sender
        if message.payloadtype == Packet.PayloadType.CONNECT:
            # CONNECT
            pass

        elif message.payloadtype == Packet.PayloadType.DISCONNECT:
            # DISCONNECT
            pass

        elif message.payloadtype == Packet.PayloadType.HEARTBEAT:
            # HEARTBEAT
            pass

        elif message.payloadtype == Packet.PayloadType.CHAT:
            # CHAT
            pass

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")
