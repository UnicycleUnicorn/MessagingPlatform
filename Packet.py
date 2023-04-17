from enum import Enum
import time
import secrets
import math
from typing import List


class HeaderFormat:
    """
    A formatted header object - contains information about the packet & message
    """

    LENGTH = 0

    def __init__(self, length: int):
        self.length = length
        self.offset = HeaderFormat.LENGTH
        HeaderFormat.LENGTH += self.length

    def get_from(self, arr: bytearray):
        return arr[self.offset: self.offset + self.length]

    def set_to(self, arr: bytearray, item: bytearray):
        arr[self.offset: self.offset + self.length] = item


class FooterFormat:
    """
    A formatted footer object - contains primarily metadata about the payload
    """

    LENGTH = 0

    def __init__(self, length: int):
        self.length = length
        self.offset = FooterFormat.LENGTH
        FooterFormat.LENGTH += self.length

    def get_from(self, arr: bytearray):
        return arr[self.offset: self.offset + self.length]

    def set_to(self, arr: bytearray, item: bytearray):
        arr[self.offset: self.offset + self.length] = item


class PayloadType(Enum):
    """
    Type / format of message in the packet:
        * CONNECT\n
        * DISCONNECT\n
        * HEARTBEAT\n
        * CHAT
    """

    CONNECT = 0
    DISCONNECT = 1
    HEARTBEAT = 2
    CHAT = 3

    def __new__(cls, value: int):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.bytes_value = value.to_bytes(length=Footer.PAYLOAD_TYPE.length, byteorder='big')
        return obj

    @classmethod
    def from_bytes(cls, b: bytes) -> 'PayloadType':
        for mtype in cls:
            if mtype.bytes_value == b:
                return mtype
        raise ValueError(f"No MessageType with value {b}")

    def to_bytes(self):
        return self.bytes_value


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
        arr = bytearray(b'\x00' * HeaderFormat.LENGTH)

        Header.MESSAGE_ID.set_to(arr, bytearray(self.messageid))

        packetcount = self.packetcount.to_bytes(length=Header.PACKET_COUNT.length, byteorder='big')
        Header.PACKET_COUNT.set_to(arr, bytearray(packetcount))

        packetsequencenumber = self.packetsequencenumber.to_bytes(length=Header.PACKET_SEQUENCE_NUMBER.length, byteorder='big')
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
        return f"HEADER:\n    MessageID: {self.messageid}\n    PacketCount: {self.packetcount}\n    SequenceNumber: {self.packetsequencenumber}\n"


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
        arr = bytearray(b'\x00' * FooterFormat.LENGTH)

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
        return f"FOOTER:\n    PayloadType: {self.payloadtype}\n    UserID: {self.userid}\n    UnixTime: {self.unixtime}\n"


class Packet:
    MAX_PACKET_SIZE = 512

    def __init__(self, header: Header, payload: 'Payload', footer: Footer = None):
        self.header = header
        self.payload = payload
        self.footer = footer

    def to_bytes(self) -> bytes:
        if self.footer is None:
            return self.header.to_bytes() + self.payload.to_bytes()
        else:
            return self.header.to_bytes() + self.payload.to_bytes() + self.footer.to_bytes()

    @classmethod
    def from_bytes(cls, packet: bytes) -> 'Packet':
        header = Header.from_bytes(packet[:HeaderFormat.LENGTH])
        footer = None
        payload: Payload
        if header.packetcount == header.packetsequencenumber + 1:
            footerstart = len(packet) - FooterFormat.LENGTH
            payload = Payload.from_bytes(packet[HeaderFormat.LENGTH:footerstart])
            footer = Footer.from_bytes(packet[footerstart:])
        else:
            payload = Payload.from_bytes(packet[HeaderFormat.LENGTH:])

        return Packet(header, payload, footer)

    def __str__(self):
        if self.footer is None:
            return self.header.__str__() + self.payload.__str__()
        else:
            return self.header.__str__() + self.payload.__str__() + self.footer.__str__()


class Payload:
    MAX_PAYLOAD_SIZE_NO_FOOTER = Packet.MAX_PACKET_SIZE - HeaderFormat.LENGTH
    MAX_PAYLOAD_SIZE_FOOTER = MAX_PAYLOAD_SIZE_NO_FOOTER - FooterFormat.LENGTH

    def __init__(self, message: bytes):
        self.message = message

    def to_bytes(self) -> bytes:
        return self.message

    @staticmethod
    def from_bytes(message: bytes):
        return Payload(message)

    def __str__(self) -> str:
        return f"PAYLOAD:\n    {self.message}\n"


class Message:
    def __init__(self, payload: bytes, payloadtype: PayloadType, userid: int, messageid: bytes = None, _packetcount: int = None, _unixtime=None):
        if messageid is None:  # If message id is none, assume new message and create a random id
            messageid = secrets.token_bytes(Header.MESSAGE_ID.length)

        self.messageid = messageid
        if _packetcount is None:
            self.packetcount = math.ceil(
                (len(payload) + FooterFormat.LENGTH) / (Packet.MAX_PACKET_SIZE - HeaderFormat.LENGTH))
        else:
            self.packetcount = _packetcount

        self.payload = payload

        self.payloadtype = payloadtype
        self.userid = userid

        if _unixtime is None:
            self.unixtime = int(time.time())
        else:
            self.unixtime = _unixtime

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

    @classmethod
    def from_bytes_list(cls, byteslist: List[bytes]) -> 'Message':
        payload = b''
        count = len(byteslist)
        for i in range(count - 1):
            payload += byteslist[i][HeaderFormat.LENGTH:]

        packet = Packet.from_bytes(byteslist[count - 1])
        payload += packet.payload.to_bytes()
        return Message(payload, packet.footer.payloadtype, packet.footer.userid, packet.header.messageid, packet.header.packetcount, packet.footer.unixtime)
