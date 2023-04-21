import threading
from collections import OrderedDict
from typing import List, Tuple
from typing import OrderedDict as Od
import time
import Packet


class MessageReconstructor:
    def __init__(self):
        self.recondict: Od[bytes, List[List[Packet.Packet], Tuple[str, int], int]] = OrderedDict()
        self.lock = threading.Lock()

    def received_packet(self, packet: Packet, sender: Tuple[str, int]) -> Packet.Message | None:
        if packet.header.packetcount == 1:
            return Packet.Message.from_packet_list([packet], sender)
        else:
            self.lock.acquire()
            if self.__in_dictionary__(packet):
                packets = self.__old_dictionary_entry__(packet)
                self.lock.release()
                if packets is None:
                    return None
                else:
                    return Packet.Message.from_packet_list(packets, sender)
            else:
                self.__new_dictionary_entry__(packet, sender)
                self.lock.release()
                return None

    @staticmethod
    def create_response_time(nanoseconds: int) -> int:
        return time.time_ns() + nanoseconds

    def edit_response_time(self, messageid: bytes, nanoseconds: int) -> bool:
        responsetime = MessageReconstructor.create_response_time(nanoseconds)
        self.lock.acquire()
        if messageid in self.recondict:
            self.recondict[messageid][2] = responsetime
            self.lock.release()
            return True
        else:
            self.lock.release()
            return False

    def look_for_missing_packets(self) -> List[Tuple[List[int], bytes, Tuple[str, int]]]:
        self.lock.acquire()
        current = time.time_ns()
        missing: List[Tuple[List[int], bytes, Tuple[str, int]]] = []
        for messageid, value in self.recondict.items():
            packets, sender, t = value
            if t < current:
                missing.append(([i for i, x in enumerate(packets) if x is None], messageid, sender))
        self.lock.release()
        return missing

    # dictionary wrappers
    def __in_dictionary__(self, packet: Packet) -> bool:
        return packet.header.messageid in self.recondict

    def __new_dictionary_entry__(self, packet: Packet, sender: Tuple[str, int]):
        reconlist = [None] * packet.header.packetcount
        reconlist[packet.header.packetsequencenumber] = packet
        self.recondict[packet.header.messageid] = [reconlist, sender, MessageReconstructor.create_response_time(50000000)]

    def __old_dictionary_entry__(self, packet: Packet) -> List[Packet.Packet] | None:
        reconlist = self.recondict[packet.header.messageid][0]
        self.recondict[packet.header.messageid][2] = MessageReconstructor.create_response_time(50000000)
        reconlist[packet.header.packetsequencenumber] = packet
        if None in reconlist:
            return None
        else:
            return self.recondict.pop(packet.header.messageid, None)[0]
