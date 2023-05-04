import NetworkCommunicationConstants
import NetworkHandler
import Packet
from typing import Tuple
import BetterLog
import threading
from EncryptionHandler import EncryptionHandler


class Client:
    def __init__(self, serverip: str, user_id: int, port: int = 8888):
        self.handler = NetworkHandler.NetworkHandler(port, self.__recv__, user_id, host=serverip)
        self.user_id = user_id
        self.encryption_handler = EncryptionHandler()

        t = threading.Thread(target=self.generate_dh_and_send_public)
        t.daemon = True
        t.start()

        self.handler.send_message(Packet.Message(b'', Packet.PayloadType.CONNECT, self.user_id), None)
        threading.Timer(NetworkCommunicationConstants.HEARTBEAT_FREQUENCY_S, self.send_heartbeat).start()

    def generate_dh_and_send_public(self):
        dh_public = self.encryption_handler.generate_dh_keys()
        message = Packet.Message(dh_public, Packet.PayloadType.DH_KEY, self.user_id)
        self.handler.send_message(message, None)

    def generate_aes_gcm_and_send_prepared(self, other_public_key: bytes):
        self.encryption_handler.received_other_public_key(other_public_key)
        self.encryption_handler.self_prepared = True
        message = Packet.Message(b'', Packet.PayloadType.PREPARED, self.user_id)
        self.handler.send_message(message, None)

    def send_heartbeat(self):
        message = Packet.Message(b'', Packet.PayloadType.HEARTBEAT, self.user_id)
        self.handler.send_message(message, None)

        # Create a timer to re-call this method in N ns
        threading.Timer(NetworkCommunicationConstants.HEARTBEAT_FREQUENCY_S, self.send_heartbeat).start()

    def send(self, message: str):
        if self.encryption_handler.is_prepared():
            message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, self.user_id)
            self.handler.send_message(message, None)
        else:
            BetterLog.log_text('COULD NOT SEND MESSAGE: ENCRYPTION NOT READY')

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

        elif message.payloadtype == Packet.PayloadType.DH_KEY:
            # DH KEY
            t = threading.Thread(target=self.generate_aes_gcm_and_send_prepared, args=(message.payload,))
            t.daemon = True
            t.start()

        elif message.payloadtype == Packet.PayloadType.PREPARED:
            # PREPARED
            self.encryption_handler.other_prepared = True

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")
