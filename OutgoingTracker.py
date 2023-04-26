import threading
import time
from collections import OrderedDict
from typing import OrderedDict as Od
from typing import List, Tuple

import BetterLog
import NetworkCommunicationConstants


class OutgoingTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.sentdictionary: Od[bytes, List[List[bytes], Tuple[str, int], int, None | List[int]]] = OrderedDict()

    @staticmethod
    def create_resend_time(nanoseconds: int) -> int:
        return time.time_ns() + nanoseconds

    def close(self, messageid: bytes):
        self.lock.acquire()
        self.sentdictionary.pop(messageid, None)
        self.lock.release()
        BetterLog.log_text(f"CLOSED MESSAGE: {messageid}")

    def sent(self, messageid: bytes, packets: List[bytes], recipient: Tuple[str, int]) -> bool:
        self.lock.acquire()
        if self.__in_dictionary__(messageid):
            self.lock.release()
            return False
        self.sentdictionary[messageid] = [packets, recipient, OutgoingTracker.create_resend_time(75000000), None]
        self.lock.release()
        BetterLog.log_text(f"STARTED MESSAGE: {messageid}")
        return True

    def get_packets(self, messageid: bytes, packets: List[int]) -> List[bytes] | None:
        self.lock.acquire()
        if self.__in_dictionary__(messageid):
            self.sentdictionary[messageid][3] = packets
            bytepacks = self.sentdictionary[messageid][0]
            resends = [bytepacks[i] for i in packets]
            self.lock.release()
            return resends
        else:
            self.lock.release()
            return None

    def resent(self, messageid: bytes, nanoseconds: int = NetworkCommunicationConstants.WAIT_RESPONSE_TIME_NS) -> bool:
        self.lock.acquire()
        if self.__in_dictionary__(messageid):
            self.lock.release()
            return False
        self.sentdictionary[messageid][2] = OutgoingTracker.create_resend_time(nanoseconds)
        self.lock.release()
        return True

    def find_resends(self) -> List[Tuple[bytes, List[bytes], Tuple[str, int]]]:
        self.lock.acquire()
        current = time.time_ns()
        missing: List[Tuple[bytes, List[bytes], Tuple[str, int]]] = []
        for messageid, value in self.sentdictionary.items():
            packets, recipient, t, packetlist = value
            if t < current:
                if packetlist is None:
                    missing.append((messageid, packets, recipient))
                else:
                    missing.append((messageid, [packets[i] for i in packetlist], recipient))
        self.lock.release()
        return missing

    def __in_dictionary__(self, messageid: bytes) -> bool:
        return messageid in self.sentdictionary
