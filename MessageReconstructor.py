import Packet
from typing import OrderedDict as Od
from typing import List, Tuple
from collections import OrderedDict


class MessageReconstructor:
    def __init__(self):
        self.recondict: Od[bytes, List[Packet.Packet]] = OrderedDict()

    def received_packet(self, packet: Packet, sender: Tuple[str, int]) -> Packet.Message | None:
        if packet.header.packetcount == 1:
            return Packet.Message.from_packet_list([packet], sender)
        else:
            if self.__in_dictionary__(packet):
                packets = self.__old_dictionary_entry__(packet)
                if packets is None:
                    return None
                else:
                    return Packet.Message.from_packet_list(packets, sender)
            else:
                self.__new_dictionary_entry__(packet)
                return None

    # dictionary wrappers
    def __in_dictionary__(self, packet: Packet) -> bool:
        return packet.header.messageid in self.recondict

    def __new_dictionary_entry__(self, packet: Packet):
        reconlist = [None] * packet.header.packetcount
        reconlist[packet.header.packetsequencenumber] = packet
        self.recondict[packet.header.messageid] = reconlist

    def __old_dictionary_entry__(self, packet: Packet) -> List[Packet.Packet] | None:
        reconlist = self.recondict[packet.header.messageid]
        reconlist[packet.header.packetsequencenumber] = packet
        if None in reconlist:
            return None
        else:
            return self.recondict.pop(packet.header.messageid, None)
