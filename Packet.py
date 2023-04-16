from enum import Enum
import time
import secrets


class HeaderFormat:
    """
    A formatted header object. ...MESSAGE_ID or MESSAGE_LENGTH
    """

    TOTAL_LENGTH = 0

    def __init__(self, length: int):
        self.length = length
        self.offset = HeaderFormat.TOTAL_LENGTH
        HeaderFormat.TOTAL_LENGTH += self.length

    def get_from(self, arr: bytearray):
        return arr[self.offset: self.offset + self.length]

    def set_to(self, arr: bytearray, item: bytearray):
        arr[self.offset: self.offset + self.length] = item


MESSAGE_ID = HeaderFormat(3)        # bytes
MESSAGE_TYPE = HeaderFormat(1)      # MessageType
MESSAGE_LENGTH = HeaderFormat(4)    # int
USER_ID = HeaderFormat(4)           # int
UNIX_TIME = HeaderFormat(4)         # int


class MessageType(Enum):
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
        obj.bytes_value = value.to_bytes(length=MESSAGE_TYPE.length, byteorder='big')
        return obj

    @classmethod
    def from_bytes(cls, b: bytes) -> 'MessageType':
        for mtype in cls:
            if mtype.bytes_value == b:
                return mtype
        raise ValueError(f"No MessageType with value {b}")
    
    def to_bytes(self):
        return self.bytes_value


class PacketHeader:
    """
    Automatically create a packet header and transform it into a serialized object.
    this header incorporates the following fields:\n
    * Message ID - bytes representing the random message id
    * Message Length - int representing message length (bytes)
    * Message Type - MessageType representing the format of the message
    * User ID - int representing the sending users id
    * Unix Time - int representing the time the message was sent
    """
    def __init__(self, messageid: bytes, messagetype: MessageType, messagelength: int, userid: int, unixtime: int):
        self.messageid = messageid
        self.messagelength = messagelength
        self.messagetype = messagetype
        self.userid = userid
        self.unixtime = unixtime

    def to_bytes(self) -> bytes:
        """
        Converts this packet into it's byte represented form that can be stored or sent over the network.
        """
        arr = bytearray(b'\x00' * HeaderFormat.TOTAL_LENGTH)

        MESSAGE_ID.set_to(arr, bytearray(self.messageid))

        MESSAGE_TYPE.set_to(arr, bytearray(self.messagetype.to_bytes()))

        messagelength = self.messagelength.to_bytes(length=MESSAGE_LENGTH.length, byteorder='big')
        MESSAGE_LENGTH.set_to(arr, bytearray(messagelength))

        userid = self.userid.to_bytes(length=USER_ID.length, byteorder='big')
        USER_ID.set_to(arr, bytearray(userid))

        unixtime = self.unixtime.to_bytes(length=UNIX_TIME.length, byteorder='big')
        UNIX_TIME.set_to(arr, bytearray(unixtime))

        return bytes(arr)

    @classmethod
    def from_bytes(cls, header: bytes):
        """
        Constructs a PacketHeader from its byte representation
        """
        arr = bytearray(header)

        messageid = bytes(MESSAGE_ID.get_from(arr))
        messagetype = MessageType.from_bytes(bytes(MESSAGE_TYPE.get_from(arr)))
        messagelength = int.from_bytes(bytes(MESSAGE_LENGTH.get_from(arr)), byteorder='big')
        userid = int.from_bytes(bytes(USER_ID.get_from(arr)), byteorder='big')
        unixtime = int.from_bytes(bytes(UNIX_TIME.get_from(arr)), byteorder='big')

        return PacketHeader(messageid, messagetype, messagelength, userid, unixtime)

    def __str__(self) -> str:
        return f"HEADER:\n    MessageID: {self.messageid}\n    MessageType: {self.messagetype}\n    MessageLength: {self.messagelength}\n    UserID: {self.userid}\n    UnixTime: {self.unixtime}\n"


class PacketMessage:
    def __init__(self, message: str):
        self.message = message

    def to_bytes(self) -> bytes:
        return self.message.encode()

    @staticmethod
    def from_bytes(message: bytes):
        return PacketMessage(message.decode())

    def __str__(self) -> str:
        return f"MESSAGE:\n    {self.message}\n"


class Packet:
    def __init__(self, header: PacketHeader, message: PacketMessage):
        self.header = header
        self.message = message

    @classmethod
    def construct(cls, message: str):
        packmessage = PacketMessage(message)
        packheader = PacketHeader(secrets.token_bytes(MESSAGE_ID.length), MessageType.CHAT, len(packmessage.to_bytes()), 1563, int(time.time()))
        return Packet(packheader, packmessage)

    def to_bytes(self) -> bytes:
        return self.header.to_bytes() + self.message.to_bytes()

    def __str__(self):
        return self.header.__str__() + self.message.__str__()
