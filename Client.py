import NetworkHandler
import Packet
from typing import Tuple
import BetterLog


class Client:
    def __init__(self, serverip: str, user_id: int, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__, user_id, host=serverip)
        self.user_id = user_id
        self.handler.send_message(Packet.Message(b'', Packet.PayloadType.CONNECT, self.user_id), None)

    def send(self, message: str):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, self.user_id)
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
            if message.userid == self.user_id:
                BetterLog.log_message_text(message.payload.decode(), str(message.userid), True)
            else:
                BetterLog.log_message_text(message.payload.decode(), str(message.userid))

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")
