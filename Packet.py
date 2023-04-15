class HeaderFormat:
    TOTAL_LENGTH = 0

    def __init__(self, length: int):
        self.length = length
        self.offset = HeaderFormat.TOTAL_LENGTH
        HeaderFormat.TOTAL_LENGTH += self.length

    def getfromarr(self, arr: bytearray):
        return arr[self.offset: self.offset + self.length]

    def settoarr(self, arr: bytearray, item: bytearray):
        arr[self.offset: self.offset + self.length] = item


MESSAGE_LENGTH = HeaderFormat(4)


class PacketHeader:
    def __init__(self, messagelength: int):
        self.messagelength = messagelength

    def tobytes(self) -> bytes:
        arr = bytearray(b'\x00' * HeaderFormat.TOTAL_LENGTH)
        messagelength = self.messagelength.to_bytes(length=MESSAGE_LENGTH.length, byteorder='big')
        MESSAGE_LENGTH.settoarr(arr, bytearray(messagelength))
        return bytes(arr)

    @staticmethod
    def frombytes(header: bytes):
        arr = bytearray(header)
        messagelength = bytes(MESSAGE_LENGTH.getfromarr(arr))
        return PacketHeader(int.from_bytes(messagelength, byteorder='big'))


class PacketMessage:
    def __init__(self, message: str):
        self.message = message

    def tobytes(self) -> bytes:
        return self.message.encode()

    @staticmethod
    def frombytes(message: bytes):
        return PacketMessage(message.decode())


class Packet:
    def __init__(self, header: PacketHeader, message: PacketMessage):
        self.header = header
        self.message = message

    @staticmethod
    def construct(message: str):
        packmessage = PacketMessage(message)
        packheader = PacketHeader(len(packmessage.tobytes()))
        return Packet(packheader, packmessage)

    def tobytes(self) -> bytes:
        return self.header.tobytes() + self.message.tobytes()
