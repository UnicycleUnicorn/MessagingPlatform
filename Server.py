import logging
import NetworkHandler
import Packet
from typing import Tuple


class Server:
    def __init__(self, port: int):
        self.handler = NetworkHandler.NetworkHandler(port)
        self.handler.add_listener(self.__recv__)

    def send(self, message: str, recipient: Tuple[str, int]):
        packet = Packet.Packet.construct(message)
        if self.handler.send(packet, recipient):
            logging.info("SENT PACKET\n")
        else:
            logging.info("UNABLE TO SEND PACKET\n")

    def __recv__(self, sender: Tuple[str, int], packet: Packet.Packet):
        logging.info("======== RECEIVED PACKET ========")
        logging.info(packet.__str__())
        logging.info("")
        self.send("SERVER RECEIVED PACKET", sender)
