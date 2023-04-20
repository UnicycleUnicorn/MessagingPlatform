import logging

import Packet

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)


def __log__(item: str):
    logging.info(item)


def __log_packet__(packet: Packet.Packet) -> str:
    return packet.__str__() + '\n'


def __log_message(message: Packet.Message) -> str:
    return message.payload.decode() + '\n'


def __start_section__(item: str) -> str:
    return '======= ' + item + ' =======' + '\n'


def __end_section__(i: int) -> str:
    return "-" * i + '\n' * 2


def sent_packet(packet: Packet.Packet):
    s = __start_section__("SENT PACKET")
    __log__(s + __log_packet__(packet) + __end_section__(len(s)))


def failed_to_send_packet(packet: Packet.Packet, e: Exception):
    s = __start_section__("FAILED TO SEND PACKET")
    __log__(s + __log_packet__(packet) + f"{e}\n" + __end_section__(len(s)))


def received_packet(packet: Packet.Packet):
    s = __start_section__("RECEIVED PACKET")
    __log__(s + __log_packet__(packet) + __end_section__(len(s)))


def received_message(message: Packet.Message):
    s = __start_section__("RECEIVED MESSAGE")
    __log__(s + __log_message(message) + __end_section__(len(s)))


def sent_message(message: Packet.Message):
    s = __start_section__("SENT MESSAGE")
    __log__(s + __log_message(message) + __end_section__(len(s)))


def failed_to_send_message(message: Packet.Message):
    s = __start_section__("FAILED TO SEND MESSAGE")
    __log__(s + __log_message(message) + __end_section__(len(s)))
