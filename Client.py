import logging
import Packet
import NetworkHandler
from typing import Tuple


class Client:
    def __init__(self, port: int, serverip: str):
        self.handler = NetworkHandler.NetworkHandler(port, host=serverip)
        self.handler.add_listener(self.__recv__)

    def send(self, message: str):
        message = Packet.Message(message.encode(), Packet.PayloadType.CHAT, 69420)
        if self.handler.send_message(message):
            logging.info("SENT MESSAGE\n")
        else:
            logging.info("UNABLE TO SEND MESSAGE\n")

    def __recv__(self, sender: Tuple[str, int], packet: Packet.Packet):
        logging.info("======== RECEIVED PACKET ========")
        logging.info(packet.__str__())
        logging.info("")
