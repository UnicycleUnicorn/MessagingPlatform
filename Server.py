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

    def generate_dh_and_send_public(self, client: Tuple[str, int]):
        dh_public = self.clients.client_dictionary[client].encryption_handler.generate_dh_keys()
        self.send_message(Packet.PayloadType.DH_KEY, client, dh_public)

    def generate_aes_gcm_and_send_prepared(self, other_public_key: bytes, client: Tuple[str, int]):
        self.clients.client_dictionary[client].encryption_handler.received_other_public_key(other_public_key)
        self.clients.client_dictionary[client].encryption_handler.self_prepared = True
        self.send_message(Packet.PayloadType.PREPARED, client)

    def send_message(self, payload_type: Packet.PayloadType, recipient: Tuple[str, int], payload: bytes = b'', unix_time: None | int = None):
        if payload_type.should_encrypt():
            if self.clients.client_dictionary[recipient].encryption_handler.is_prepared():
                payload = self.clients.client_dictionary[recipient].encryption_handler.encrypt(payload)
                message = Packet.Message(payload, payload_type, self.user_id, None, None, unix_time)
                self.handler.send_message(message, recipient)
            else:
                BetterLog.log_text('COULD NOT SEND MESSAGE: ENCRYPTION NOT READY')
        else:
            message = Packet.Message(payload, payload_type, self.user_id)
            self.handler.send_message(message, recipient)

    def disconnect_inactive(self):
        self.clients.disconnect_inactive()

        # Create a timer to re-call this method in N ns
        threading.Timer(NetworkCommunicationConstants.HEARTBEAT_POLL_TIME_S, self.disconnect_inactive).start()

    def send(self, message: str, recipient: Tuple[str, int]):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, self.user_id)
        self.handler.send_message(message, recipient)

    def broadcast_text(self, text: str):
        self.broadcast(Packet.PayloadType.CHAT, text.encode(), None)

    def __recv__(self, message: Packet.Message):
        messageid: bytes = message.messageid
        sender: Tuple[str, int] = message.sender

        payload = message.payload
        if message.payloadtype.should_encrypt():
            payload = self.clients.client_dictionary[sender].encryption_handler.decrypt(message.payload)

        if message.payloadtype == Packet.PayloadType.CONNECT:
            # CONNECT
            self.clients.received_connection(sender, message.userid, message.payload)
            t = threading.Thread(target=self.generate_dh_and_send_public, args=(sender,))
            t.daemon = True
            t.start()

        elif message.payloadtype == Packet.PayloadType.DISCONNECT:
            # DISCONNECT
            self.clients.force_disconnect(sender)

        elif message.payloadtype == Packet.PayloadType.HEARTBEAT:
            # HEARTBEAT
            self.clients.received_heartbeat(sender)

        elif message.payloadtype == Packet.PayloadType.CHAT:
            # CHAT
            self.broadcast(message.payloadtype, payload, message.unixtime)

        elif message.payloadtype == Packet.PayloadType.DH_KEY:
            # DH KEY
            t = threading.Thread(target=self.generate_aes_gcm_and_send_prepared, args=(message.payload, sender))
            t.daemon = True
            t.start()

        elif message.payloadtype == Packet.PayloadType.PREPARED:
            # PREPARED
            self.clients.client_dictionary[sender].encryption_handler.other_prepared = True

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")

    def broadcast(self, payload_type: Packet.PayloadType, payload, unix_time: int | None):
        for client, connected_client in self.clients:
            self.send_message(payload_type, client, payload, unix_time)
