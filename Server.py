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
        message = Packet.Message(dh_public, Packet.PayloadType.DH_KEY, self.user_id)
        self.handler.send_message(message, client)

    def generate_aes_gcm_and_send_prepared(self, other_public_key: bytes, client: Tuple[str, int]):
        self.clients.client_dictionary[client].encryption_handler.received_other_public_key(other_public_key)
        self.clients.client_dictionary[client].encryption_handler.self_prepared = True
        message = Packet.Message(b'', Packet.PayloadType.PREPARED, self.user_id)
        self.handler.send_message(message, client)

    def disconnect_inactive(self):
        self.clients.disconnect_inactive()

        # Create a timer to re-call this method in N ns
        threading.Timer(NetworkCommunicationConstants.HEARTBEAT_POLL_TIME_S, self.disconnect_inactive).start()

    def send(self, message: str, recipient: Tuple[str, int]):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, self.user_id)
        self.handler.send_message(message, recipient)

    def broadcast_text(self, text: str):
        for client, connected_client in self.clients:
            if connected_client.encryption_handler.is_prepared():
                self.send(text, client)
            else:
                BetterLog.log_text('COULD NOT SEND MESSAGE: ENCRYPTION NOT READY')

    def __recv__(self, message: Packet.Message):
        messageid: bytes = message.messageid
        sender: Tuple[str, int] = message.sender
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
            self.broadcast(message)

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

    def broadcast(self, message: Packet.Message):
        for client, connected_client in self.clients:
            if connected_client.encryption_handler.is_prepared():
                payload = message.payload
                unixtime = message.unixtime
                user_id = message.userid
                payload_type = message.payloadtype
                mess = Packet.Message(payload, payload_type, user_id, None, None, unixtime)
                self.handler.send_message(mess, client)
            else:
                BetterLog.log_text('COULD NOT SEND MESSAGE: ENCRYPTION NOT READY')
