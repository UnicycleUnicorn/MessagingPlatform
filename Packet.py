from enum import Enum
import time
import math
from typing import List, Tuple
import random
import logging


class HeaderFormat:
    """
    A formatted header object - contains information about the packet & message
    """

    HEADER_LENGTH = 0

    def __init__(self, length: int):
        self.length = length
        self.offset = HeaderFormat.HEADER_LENGTH
        HeaderFormat.HEADER_LENGTH += self.length

    def get_from(self, arr: bytearray):
        return arr[self.offset: self.offset + self.length]

    def set_to(self, arr: bytearray, item: bytearray):
        arr[self.offset: self.offset + self.length] = item


class FooterFormat:
    """
    A formatted footer object - contains primarily metadata about the payload
    """

    FOOTER_LENGTH = 0

    def __init__(self, length: int):
        self.length = length
        self.offset = FooterFormat.FOOTER_LENGTH
        FooterFormat.FOOTER_LENGTH += self.length

    def get_from(self, arr: bytearray):
        return arr[self.offset: self.offset + self.length]

    def set_to(self, arr: bytearray, item: bytearray):
        arr[self.offset: self.offset + self.length] = item


class Header:
    """
    Automatically create a packet header and transform it into a serialized object.
    this header incorporates the following fields:\n
    * Message ID - bytes representing the random message id
    * Packet Count - int representing the number of packets in this message
    * Packet Sequence Number - int representing the sequence number of this packet
    """

    MESSAGE_ID = HeaderFormat(3)  # bytes
    PACKET_COUNT = HeaderFormat(1)  # int
    PACKET_SEQUENCE_NUMBER = HeaderFormat(1)  # int

    def __init__(self, messageid: bytes, packetcount: int, packetsequencenumber: int):
        self.messageid = messageid
        self.packetcount = packetcount
        self.packetsequencenumber = packetsequencenumber

    def to_bytes(self) -> bytes:
        """
        Converts this header into it's byte represented form that can be stored or sent over the network.
        """
        arr = bytearray(b'\x00' * HeaderFormat.HEADER_LENGTH)

        Header.MESSAGE_ID.set_to(arr, bytearray(self.messageid))

        packetcount = self.packetcount.to_bytes(length=Header.PACKET_COUNT.length, byteorder='big')
        Header.PACKET_COUNT.set_to(arr, bytearray(packetcount))

        packetsequencenumber = self.packetsequencenumber.to_bytes(length=Header.PACKET_SEQUENCE_NUMBER.length,
                                                                  byteorder='big')
        Header.PACKET_SEQUENCE_NUMBER.set_to(arr, bytearray(packetsequencenumber))

        return bytes(arr)

    @classmethod
    def from_bytes(cls, header: bytes):
        """
        Constructs a PacketHeader from its byte representation
        """
        arr = bytearray(header)

        messageid = bytes(Header.MESSAGE_ID.get_from(arr))
        packetcount = int.from_bytes(bytes(Header.PACKET_COUNT.get_from(arr)), byteorder='big')
        packetsequencenumber = int.from_bytes(bytes(Header.PACKET_SEQUENCE_NUMBER.get_from(arr)), byteorder='big')

        return Header(messageid, packetcount, packetsequencenumber)

    def __str__(self) -> str:
        return f"HEADER:\n    MessageID: {self.messageid}\n    PacketCount: {self.packetcount}\n    SequenceNumber: {self.packetsequencenumber}"


class PayloadType(Enum):
    """
    Type / format of message in the packet:
        * CONNECT\n
        * DISCONNECT
        * HEARTBEAT
        * CHAT
        * ACKNOWLEDGE
        * SELECTIVE_REPEAT
    """

    CONNECT = 0, False
    DISCONNECT = 1, False
    HEARTBEAT = 2, False
    CHAT = 3, True
    ACKNOWLEDGE = 4, False
    SELECTIVE_REPEAT = 5, False

    def __new__(cls, value: int, should_encrypt):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._should_encrypt_ = should_encrypt
        obj.bytes_value = value.to_bytes(length=1,
                                         byteorder='big')  # MAKE SURE TO CHANGE LENGTH IF PAYLOAD_TYPE LENGTH CHANGES
        return obj

    @classmethod
    def from_bytes(cls, b: bytes) -> 'PayloadType':
        for mtype in cls:
            if mtype.bytes_value == b:
                return mtype
        raise ValueError(f"No MessageType with value {b}")

    def to_bytes(self):
        return self.bytes_value

    def should_encrypt(self):
        return self._should_encrypt_


class Footer:
    """
    Automatically create a packet footer and transform it into a serialized object.
    this footer incorporates the following fields:\n
    * Message Type - MessageType representing the format of the message
    * User ID - int representing the sending users id
    * Unix Time - int representing the time the message was sent
    """

    PAYLOAD_TYPE = FooterFormat(1)  # PayloadType
    USER_ID = FooterFormat(4)  # int
    UNIX_TIME = FooterFormat(4)  # int

    def __init__(self, payloadtype: PayloadType, userid: int, unixtime: int):
        self.payloadtype = payloadtype
        self.userid = userid
        self.unixtime = unixtime

    def to_bytes(self) -> bytes:
        """
        Converts this footer into it's byte represented form that can be stored or sent over the network.
        """
        arr = bytearray(b'\x00' * FooterFormat.FOOTER_LENGTH)

        Footer.PAYLOAD_TYPE.set_to(arr, bytearray(self.payloadtype.to_bytes()))

        userid = self.userid.to_bytes(length=Footer.USER_ID.length, byteorder='big')
        Footer.USER_ID.set_to(arr, bytearray(userid))

        unixtime = self.unixtime.to_bytes(length=Footer.UNIX_TIME.length, byteorder='big')
        Footer.UNIX_TIME.set_to(arr, bytearray(unixtime))

        return bytes(arr)

    @classmethod
    def from_bytes(cls, footer: bytes):
        """
        Constructs a PacketFooter from its byte representation
        """
        arr = bytearray(footer)
        payloadtype = PayloadType.from_bytes(bytes(Footer.PAYLOAD_TYPE.get_from(arr)))
        userid = int.from_bytes(bytes(Footer.USER_ID.get_from(arr)), byteorder='big')
        unixtime = int.from_bytes(bytes(Footer.UNIX_TIME.get_from(arr)), byteorder='big')

        return Footer(payloadtype, userid, unixtime)

    def __str__(self) -> str:
        return f"FOOTER:\n    PayloadType: {self.payloadtype}\n    UserID: {self.userid}\n    UnixTime: {self.unixtime}"


class Packet:
    MAX_PACKET_SIZE = 982

    def __init__(self, header: Header, payload: bytes, footer: Footer = None):
        self.header = header
        self.payload = payload
        self.footer = footer

    def to_bytes(self) -> bytes:
        if self.footer is None:
            return self.header.to_bytes() + self.payload
        else:
            return self.header.to_bytes() + self.payload + self.footer.to_bytes()

    @classmethod
    def from_bytes(cls, packet: bytes) -> 'Packet':
        header = Header.from_bytes(packet[:HeaderFormat.HEADER_LENGTH])
        footer = None
        payload: bytes
        if header.packetcount == header.packetsequencenumber + 1:
            footerstart = len(packet) - FooterFormat.FOOTER_LENGTH
            payload = packet[HeaderFormat.HEADER_LENGTH:footerstart]
            footer = Footer.from_bytes(packet[footerstart:])
        else:
            payload = packet[HeaderFormat.HEADER_LENGTH:]
        return Packet(header, payload, footer)

    def __str__(self):
        if self.footer is None:
            return self.header.__str__() + "\n" + f"PAYLOAD:\n    {self.payload}"
        else:
            return self.header.__str__() + "\n" + f"PAYLOAD:\n    {self.payload}" + "\n" + self.footer.__str__()


class Message:
    MAX_PAYLOAD_SIZE_NO_FOOTER = Packet.MAX_PACKET_SIZE - HeaderFormat.HEADER_LENGTH

    def __init__(self, payload: bytes, payloadtype: PayloadType, userid: int, messageid: bytes = None,
                 _packetcount: int = None, _unixtime=None, sender: Tuple[str, int] = None):
        if messageid is None:  # If message id is none, assume new message and create a random id
            messageid = random.getrandbits(8 * Header.MESSAGE_ID.length).to_bytes(length=Header.MESSAGE_ID.length,
                                                                                  byteorder='big')
        self.messageid = messageid
        if _packetcount is None:
            self.packetcount = math.ceil(
                (len(payload) + FooterFormat.FOOTER_LENGTH) / (Packet.MAX_PACKET_SIZE - HeaderFormat.HEADER_LENGTH))
        else:
            self.packetcount = _packetcount

        self.payload = payload

        self.payloadtype = payloadtype
        self.userid = userid

        if _unixtime is None:
            self.unixtime = int(time.time())
        else:
            self.unixtime = _unixtime

        self.sender = sender

    """
    def to_bytes_list(self) -> List[bytes]:
        byteslist: List[bytes] = [None] * self.packetcount
        header = Header(self.messageid, self.packetcount, 0)

        # CONSTRUCT MIDDLE PACKETS
        for psn in range(self.packetcount - 1):
            payloadstart = psn * Payload.MAX_PAYLOAD_SIZE_NO_FOOTER
            header.packetsequencenumber = psn
            packet = Packet(header,
                            Payload(self.payload[payloadstart:payloadstart + Payload.MAX_PAYLOAD_SIZE_NO_FOOTER]))
            byteslist[psn] = packet.to_bytes()

        # CONSTRUCT LAST PACKET
        header.packetsequencenumber = self.packetcount - 1
        footer = Footer(self.payloadtype, self.userid, self.unixtime)
        packet = Packet(header, Payload(self.payload[(self.packetcount - 1) * Payload.MAX_PAYLOAD_SIZE_NO_FOOTER:]),
                        footer)
        byteslist[self.packetcount - 1] = packet.to_bytes()

        return byteslist
    """

    def to_packet_list(self) -> List[Packet]:
        packetlist: List[Packet] = [None] * self.packetcount

        # CONSTRUCT MIDDLE PACKETS
        for psn in range(self.packetcount - 1):
            payloadstart = psn * Message.MAX_PAYLOAD_SIZE_NO_FOOTER
            packetlist[psn] = Packet(Header(self.messageid, self.packetcount, psn),
                                     self.payload[payloadstart:payloadstart + Message.MAX_PAYLOAD_SIZE_NO_FOOTER])

        # CONSTRUCT LAST PACKET
        packetlist[self.packetcount - 1] = Packet(Header(self.messageid, self.packetcount, self.packetcount - 1), self.payload[
                                                          (self.packetcount - 1) * Message.MAX_PAYLOAD_SIZE_NO_FOOTER:],Footer(self.payloadtype, self.userid, self.unixtime))

        return packetlist

    def __str__(self):
        header = f"METADATA:\n    MessageID: {self.messageid}\n    PacketCount: {self.packetcount}\n    UserID: {self.userid}\n    PayloadType: {self.payloadtype}\n    UnixTime: {self.unixtime}\n    Sender: {self.sender}"
        payload = f"PAYLOAD:\n    Payload: {self.payload}"
        return header + '\n' + payload

    """
    @classmethod
    def from_bytes_list(cls, byteslist: List[bytes]) -> 'Message':
        payload = b''
        count = len(byteslist)
        for i in range(count - 1):
            payload += byteslist[i][HeaderFormat.LENGTH:]

        packet = Packet.from_bytes(byteslist[count - 1])
        payload += packet.payload.to_bytes()
        return Message(payload, packet.footer.payloadtype, packet.footer.userid, packet.header.messageid, packet.header.packetcount, packet.footer.unixtime)
    """

    @classmethod
    def from_packet_list(cls, packetlist: List[Packet], sender: Tuple[str, int] = None) -> 'Message':
        payload = b''
        for packet in packetlist:
            payload += packet.payload
        footer = packetlist[-1].footer
        header = packetlist[-1].header
        return Message(payload, footer.payloadtype, footer.userid, header.messageid, header.packetcount,
                       footer.unixtime, sender=sender)
