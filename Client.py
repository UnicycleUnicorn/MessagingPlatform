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
        self.encryption_handler = EncryptionHandler(None)

        self.handler.send_message(
            Packet.Message(self.encryption_handler.dh_parameters_bytes, Packet.PayloadType.CONNECT, self.user_id), None)

        t = threading.Thread(target=self.generate_dh_and_send_public)
        t.daemon = True
        t.start()

        threading.Timer(NetworkCommunicationConstants.HEARTBEAT_FREQUENCY_S, self.send_heartbeat).start()

    def generate_dh_and_send_public(self):
        dh_public, is_prepared = self.encryption_handler.generate_dh_keys()
        self.send_message(Packet.PayloadType.DH_KEY, dh_public)
        if is_prepared:
            self.send_message(Packet.PayloadType.PREPARED)

    def receive_other_dh_public(self, other_public_key: bytes):
        is_prepared = self.encryption_handler.received_other_public_key(other_public_key)
        if is_prepared:
            self.send_message(Packet.PayloadType.PREPARED)

    def send_message(self, payload_type: Packet.PayloadType, payload: bytes = b''):
        if payload_type.should_encrypt():
            if self.encryption_handler.is_prepared():
                payload = self.encryption_handler.encrypt(payload)
                message = Packet.Message(payload, payload_type, self.user_id)
                self.handler.send_message(message, None)
            else:
                BetterLog.log_text('COULD NOT SEND MESSAGE: ENCRYPTION NOT READY')
        else:
            message = Packet.Message(payload, payload_type, self.user_id)
            self.handler.send_message(message, None)

    def send_heartbeat(self):
        self.send_message(Packet.PayloadType.HEARTBEAT)

        # Create a timer to re-call this method in N ns
        threading.Timer(NetworkCommunicationConstants.HEARTBEAT_FREQUENCY_S, self.send_heartbeat).start()

    def send(self, message: str):
        self.send_message(Packet.PayloadType.CHAT, message.encode())

    def __recv__(self, message: Packet.Message):
        messageid: bytes = message.messageid
        sender: Tuple[str, int] = message.sender

        payload = message.payload
        if message.payloadtype.should_encrypt():
            payload = self.encryption_handler.decrypt(message.payload)

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
                BetterLog.log_message_text(payload.decode(), str(message.userid), True)
            else:
                BetterLog.log_message_text(payload.decode(), str(message.userid))

        elif message.payloadtype == Packet.PayloadType.DH_KEY:
            # DH KEY
            t = threading.Thread(target=self.receive_other_dh_public, args=(message.payload,))
            t.daemon = True
            t.start()

        elif message.payloadtype == Packet.PayloadType.PREPARED:
            # PREPARED
            self.encryption_handler.other_prepared = True

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")
