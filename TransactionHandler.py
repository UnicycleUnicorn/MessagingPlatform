import threading
import time
from collections import OrderedDict
from typing import Tuple, List, Dict

import BetterLog
import NetworkCommunicationConstants
import Packet


def create_response_time(nanoseconds: int) -> int:
    return time.time_ns() + nanoseconds


class CompletedMessages:
    def __init__(self, maxsize: int):
        self._cache = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()

    def add(self, messageid: bytes):
        with self._lock:
            self._cache[messageid] = None
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def __contains__(self, item) -> bool:
        with self._lock:
            return item in self._cache


class TransactionRecord:
    def __init__(self, incoming: bool, arg: int | List[bytes]):
        self.is_incoming = incoming
        self.incoming: IncomingTransaction | None = None
        self.outgoing: OutgoingTransaction | None = None
        self.communicator: Tuple[str, int] | None = None
        self.lock: threading.Lock = threading.Lock()
        self.reattempts: int = 0
        if incoming:
            self.incoming = IncomingTransaction(arg)
        else:
            self.outgoing = OutgoingTransaction(arg)

    def release(self) -> bool:
        if self.lock.locked():
            self.lock.release()
            return True
        return False

    def is_overdue(self) -> bool:
        if self.is_incoming:
            return time.time_ns() > self.incoming.selective_repeat_time
        else:
            return time.time_ns() > self.outgoing.resend_time

    def recv_packet(self, packet: Packet.Packet) -> List[Packet.Packet] | None:
        self.incoming.recv_packet(packet)
        self.reattempts = 0
        if self.incoming.is_completed():
            return self.incoming.received
        return None

    def sent_repeat(self):
        self.reattempts += 1
        self.incoming.selective_repeat_time = create_response_time(NetworkCommunicationConstants.WAIT_RESPONSE_TIME_NS)

    def resent(self):
        self.reattempts += 1
        self.outgoing.resend_time = create_response_time(NetworkCommunicationConstants.WAIT_RESPONSE_TIME_NS)


class LockedDictionary:
    def __init__(self):
        self._dict: Dict[bytes, TransactionRecord] = {}
        self._master_lock = threading.Lock()

    def find_repeats_resends_and_fails(self) -> Tuple[
        List[Tuple[List[int], Tuple[str, int], bytes]], List[Tuple[List[bytes], Tuple[str, int], bytes]], List[bytes]]:
        repeats: List[Tuple[List[int], Tuple[str, int], bytes]] = []
        resends: List[Tuple[List[bytes], Tuple[str, int], bytes]] = []
        fails: List[bytes] = []
        with self._master_lock:
            for message_id, transaction_record in self._dict.items():
                if transaction_record.is_overdue():
                    if transaction_record.reattempts >= NetworkCommunicationConstants.GIVE_UP_REATTEMPTS:
                        fails.append(message_id)
                        BetterLog.log_text(f"Transaction Failed (Surpassed Attempt Maximum): {message_id}")
                    else:
                        if transaction_record.is_incoming:
                            repeat: Tuple[List[int], Tuple[str, int], bytes] = (
                                transaction_record.incoming.find_missing(), transaction_record.communicator, message_id)
                            repeats.append(repeat)
                            BetterLog.log_text(f"Did Not Receive Full Message (Sending Repeat): {message_id}")
                        else:
                            resend: Tuple[List[bytes], Tuple[str, int], bytes] = (
                                transaction_record.outgoing.bytepackets, transaction_record.communicator, message_id)
                            resends.append(resend)
                            BetterLog.log_text(
                                f"Did Not Receive form of Acknowledgement (Resending Packets): {message_id}")
                transaction_record.release()
        return repeats, resends, fails

    def __getitem__(self, key: bytes) -> TransactionRecord | None:
        with self._master_lock:
            if key in self._dict:
                value = self._dict[key]
                value.lock.acquire()
                return value
            return None

    def __setitem__(self, key: bytes, value: TransactionRecord):
        with self._master_lock:
            self._dict[key] = value

    def pop(self, key: bytes) -> TransactionRecord | None:
        with self._master_lock:
            return self._dict.pop(key, None)

    def new_incoming_transaction(self, packet: Packet.Packet, sender: Tuple[str, int]):
        BetterLog.log_text(f"New Incoming Transaction Created: {packet.header.messageid}")
        transaction_record = TransactionRecord(True, packet.header.packetcount)
        transaction_record.communicator = sender
        transaction_record.recv_packet(packet)
        self._dict[packet.header.messageid] = transaction_record

    def new_outgoing_transaction(self, message_id: bytes, bytepackets: List[bytes], recipient: Tuple[str, int]):
        BetterLog.log_text(f"New Outgoing Transaction Created: {message_id}")
        with self._master_lock:
            transaction_record = TransactionRecord(False, bytepackets)
            transaction_record.communicator = recipient
            self._dict[message_id] = transaction_record

    def recv_packet(self, message_id: bytes, packet: Packet.Packet, sender: Tuple[str, int]):
        with self._master_lock:
            if message_id in self._dict:
                record = self._dict[message_id]
                packetlist = record.recv_packet(packet)
                record.release()
                message = Packet.Message.from_packet_list(packetlist, sender)
                return message
            else:
                self.new_incoming_transaction(packet, sender)
                return None

    def __contains__(self, key: bytes):
        with self._master_lock:
            return key in self._dict


class IncomingTransaction:
    def __init__(self, packet_count: int):
        self.received: List[None | Packet.Packet] = [None] * packet_count
        self.selective_repeat_time = create_response_time(
            NetworkCommunicationConstants.WAIT_TIME_BEFORE_REPEAT_REQUEST_NS)

    def recv_packet(self, packet: Packet.Packet):
        self.received[packet.header.packetsequencenumber] = packet
        self.selective_repeat_time = create_response_time(
            NetworkCommunicationConstants.WAIT_TIME_BEFORE_REPEAT_REQUEST_NS)

    def is_completed(self) -> bool:
        return None not in self.received

    def find_missing(self) -> List[int]:
        return [item for item, x in enumerate(self.received) if x is None]


class OutgoingTransaction:
    def __init__(self, bytepackets: List[bytes]):
        self.bytepackets: List[bytes | None] = bytepackets
        self.resend_time = create_response_time(NetworkCommunicationConstants.WAIT_RESPONSE_TIME_NS)

    def handle_selective_repeat(self, repeats: List[int]) -> List[bytes | None]:
        # Run through the repeat and 'remove' items that were not asked for
        for i in range(len(self.bytepackets)):
            if i not in repeats:
                self.bytepackets[i] = None
        self.resend_time = create_response_time(NetworkCommunicationConstants.WAIT_RESPONSE_TIME_NS)
        return self.bytepackets


class TransactionHandler:
    def __init__(self):
        self.active = LockedDictionary()
        self.completed = CompletedMessages(NetworkCommunicationConstants.COMPLETED_MESSAGE_BUFFER_SIZE)

    def receive_packet_internal(self, packet: Packet.Packet, sender: Tuple[str, int]) -> Packet.Message | None:
        message_id = packet.header.messageid

        if message_id in self.completed:  # Packet relates to an already completed transaction
            BetterLog.log_text(f"Packet Received Relating to Completed Message {message_id}")
            return None
        BetterLog.log_packet_received(packet)
        if packet.header.packetcount == 1:  # Automatically create a message and return it if the message only has one packet
            message = Packet.Message.from_packet_list([packet], sender)
            return message

        return self.active.recv_packet(message_id, packet, sender)

    def receive_packet(self, packet: Packet.Packet, sender: Tuple[str, int]) -> Packet.Message | None:
        possible_message = self.receive_packet_internal(packet, sender)

        if possible_message is None:
            return None

        BetterLog.log_message_received(possible_message)

        return possible_message

    def sent_message(self, message_id: bytes, bytepackets: List[bytes], recipient: Tuple[str, int]):
        self.active.new_outgoing_transaction(message_id, bytepackets, recipient)

    def force_close(self, message_id: bytes) -> bool:
        self.completed.add(message_id)
        BetterLog.log_text(f"Closed Message: {message_id}")
        return bool(self.active.pop(message_id))

    def find_repeats_resends_and_fails(self) -> Tuple[
        List[Tuple[List[int], Tuple[str, int], bytes]], List[Tuple[List[bytes], Tuple[str, int], bytes]], List[bytes]]:
        return self.active.find_repeats_resends_and_fails()

    def resent(self, message_id: bytes):
        transaction_record = self.active[message_id]
        if transaction_record is None:
            return
        transaction_record.resent()
        transaction_record.release()

    def sent_repeat(self, message_id: bytes):
        transaction_record = self.active[message_id]
        if transaction_record is None:
            return
        transaction_record.sent_repeat()
        transaction_record.release()

    def recv_selective_repeat(self, message_id: bytes, repeats: List[int]) -> List[bytes | None] | None:
        transaction_record = self.active[message_id]
        if transaction_record is None:
            return None
        repeats = transaction_record.outgoing.handle_selective_repeat(repeats)
        transaction_record.reattempts = 0
        transaction_record.release()
        return repeats
