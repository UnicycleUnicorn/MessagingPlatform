from typing import Tuple, List

import NetworkHandler
import Packet
import BetterLog


class Server:
    def __init__(self, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__)
        self.clients: List[Tuple[str, int]] = []

    def send(self, message: str, recipient: Tuple[str, int]):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, 69420)
        self.handler.send_message(message, recipient)

    def add_client(self, client: Tuple[str, int]) -> bool:
        if client not in self.clients:
            self.clients.append(client)
            BetterLog.log_text(f"ADDED NEW CLIENT: {client}")
            return True
        return False

    def remove_client(self, client: Tuple[str, int]) -> bool:
        if client in self.clients:
            self.clients.remove(client)
            BetterLog.log_text(f"REMOVED CLIENT: {client}")
            return True
        return False

    def __recv__(self, message: Packet.Message):
        messageid: bytes = message.messageid
        sender: Tuple[str, int] = message.sender
        if message.payloadtype == Packet.PayloadType.CONNECT:
            # CONNECT
            self.add_client(sender)

        elif message.payloadtype == Packet.PayloadType.DISCONNECT:
            # DISCONNECT
            self.remove_client(sender)

        elif message.payloadtype == Packet.PayloadType.HEARTBEAT:
            # HEARTBEAT
            self.add_client(sender)

        elif message.payloadtype == Packet.PayloadType.CHAT:
            # CHAT
            self.broadcast(message)

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")

    def broadcast(self, message: Packet.Message):
        for client in self.clients:
            payload = message.payload
            unixtime = message.unixtime
            user_id = message.userid
            payload_type = message.payloadtype
            mess = Packet.Message(payload, payload_type, user_id, None, None, unixtime)
            self.handler.send_message(mess, client)
