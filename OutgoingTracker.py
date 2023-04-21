import threading
import time
from collections import OrderedDict
from typing import OrderedDict as Od
from typing import List, Tuple

import NetworkCommunicationConstants


class OutgoingTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.sentdictionary: Od[bytes, List[List[bytes], Tuple[str, int], int]] = OrderedDict()

    @staticmethod
    def create_resend_time(nanoseconds: int) -> int:
        return time.time_ns() + nanoseconds

    def close(self, messageid: bytes):
        self.lock.acquire()
        self.sentdictionary.pop(messageid, None)
        self.lock.release()

    def sent(self, messageid: bytes, packets: List[bytes], recipient: Tuple[str, int]) -> bool:
        self.lock.acquire()
        if self.__in_dictionary__(messageid):
            self.lock.release()
            return False
        self.sentdictionary[messageid] = [packets, recipient, OutgoingTracker.create_resend_time(75000000)]
        self.lock.release()
        return True

    def get_packets(self, messageid: bytes, packets: List[int]) -> List[bytes] | None:
        self.lock.acquire()
        if self.__in_dictionary__(messageid):
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

    """
    def find_resends(self) -> List[Tuple[List[bytes], Tuple[str, int]]]:
        self.lock.acquire()
        current = time.time_ns()
        missing: List[Tuple[List[bytes], Tuple[str, int]]] = []
        for messageid, value in self.sentdictionary.items():
            packets, sender, t = value
            if t < current:
                pass #
        self.lock.release()
        return missing
    """

    # Dictionary wrappers

    def __in_dictionary__(self, messageid: bytes) -> bool:
        return messageid in self.sentdictionary
