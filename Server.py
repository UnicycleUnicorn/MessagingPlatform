from typing import Tuple

import ConnectedClient
import NetworkCommunicationConstants
import NetworkHandler
import Packet
import BetterLog
import threading


class Server:
    def __init__(self, user_id: int = 0, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__, user_id)
        self.user_id = user_id
        self.clients: ConnectedClient.ClientList = ConnectedClient.ClientList()
        self.disconnect_inactive()

    def disconnect_inactive(self):
        self.clients.disconnect_inactive()

        # Create a timer to re-call this method in N ns
        threading.Timer(NetworkCommunicationConstants.HEARTBEAT_POLL_TIME_S, self.disconnect_inactive).start()

    def send(self, message: str, recipient: Tuple[str, int]):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, self.user_id)
        self.handler.send_message(message, recipient)

    def broadcast_text(self, text: str):
        for client in self.clients:
            self.send(text, client)

    def __recv__(self, message: Packet.Message):
        messageid: bytes = message.messageid
        sender: Tuple[str, int] = message.sender
        if message.payloadtype == Packet.PayloadType.CONNECT:
            # CONNECT
            self.clients.received_connection(sender, message.userid)

        elif message.payloadtype == Packet.PayloadType.DISCONNECT:
            # DISCONNECT
            self.clients.force_disconnect(sender)

        elif message.payloadtype == Packet.PayloadType.HEARTBEAT:
            # HEARTBEAT
            self.clients.received_heartbeat(sender)

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
