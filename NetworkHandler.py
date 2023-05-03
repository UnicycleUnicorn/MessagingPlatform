import asyncio
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Tuple
import BetterLog
import NetworkCommunicationConstants
import Packet
from TransactionHandler import TransactionHandler


class NetworkHandler:
    def __init__(self, port: int, listener: Callable[[Packet.Message], None], host: str = ''):
        # Create a transaction history handler
        self.TRANSACTION_HANDLER = TransactionHandler()
        self.find_repeats_resends_and_fails()

        self.PORT = port
        self.HOST = host
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SOCKET.bind(('', self.PORT))
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,
                               NetworkCommunicationConstants.OUTGOING_BUFFER_SIZE_BYTES)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,
                               NetworkCommunicationConstants.INCOMING_BUFFER_SIZE_BYTES)

        # Set the message listener
        self.MESSAGE_LISTENER = listener

        # Create a thread pool
        self.EXECUTOR = ThreadPoolExecutor(max_workers=6)

        # Create the loop to handle queued items
        self.INCOMING_QUEUE = asyncio.Queue(maxsize=500)
        self.INCOMING_LOOP = asyncio.new_event_loop()
        t = threading.Thread(target=self.__incoming_looper__)
        t.daemon = True
        t.start()

        # Create the queue to handle outgoing items
        self.OUTGOING_QUEUE = asyncio.Queue(maxsize=10000)
        self.OUTGOING_LOOP = asyncio.new_event_loop()
        t = threading.Thread(target=self.__outgoing_looper__)
        t.daemon = True
        t.start()

        # Listen for packets
        t = threading.Thread(target=self.__listen__)
        t.daemon = True
        t.start()

    def __incoming_looper__(self):
        asyncio.set_event_loop(self.INCOMING_LOOP)
        self.INCOMING_LOOP.create_task(self.__incoming_queue_consume())
        self.INCOMING_LOOP.run_forever()

    def __outgoing_looper__(self):
        asyncio.set_event_loop(self.OUTGOING_LOOP)
        self.OUTGOING_LOOP.create_task(self.__outgoing_queue_consume())
        self.OUTGOING_LOOP.run_forever()

    def find_repeats_resends_and_fails(self):
        repeats, resends, fails = self.TRANSACTION_HANDLER.find_repeats_resends_and_fails()

        for fail in fails:
            self.TRANSACTION_HANDLER.force_close(fail)

        for resend in resends:
            packets, recipient, message_id = resend
            for packet in packets:
                if packet is not None:
                    self.__send_packet__(packet, recipient)
            self.TRANSACTION_HANDLER.resent(message_id)

        for repeat in repeats:
            repeat_list, recipient, message_id = repeat
            message = Packet.Message(bytes(repeat_list), Packet.PayloadType.SELECTIVE_REPEAT, 64920,
                                     messageid=message_id)
            self.send_message(message, recipient=recipient, should_track=False)
            self.TRANSACTION_HANDLER.sent_repeat(message_id)

        # Create a timer to re-call this method in N ns
        threading.Timer(NetworkCommunicationConstants.FIND_RESEND_REPEAT_FAIL_POLL_TIME_S,
                        self.find_repeats_resends_and_fails).start()

    def __listen__(self):
        while True:
            asyncio.run_coroutine_threadsafe(
                self.INCOMING_QUEUE.put(self.SOCKET.recvfrom(NetworkCommunicationConstants.MAXIMUM_PACKET_SIZE_BYTES)),
                self.INCOMING_LOOP)

    async def __incoming_queue_consume(self):
        while True:
            raw_packet, sender = await self.INCOMING_QUEUE.get()
            self.EXECUTOR.submit(self.__received_packet__, raw_packet, sender)

    async def __outgoing_queue_consume(self):
        while True:
            BetterLog.log_text("CONSUMPTION")
            raw_packet, recipient = await self.OUTGOING_QUEUE.get()
            BetterLog.log_text("CONSUMED")
            self.__send_raw_packet(raw_packet, recipient)
            BetterLog.log_text("SENT")

    def __send_raw_packet(self, raw_packet: bytes, recipient: Tuple[str, int]):
        try:
            self.SOCKET.sendto(raw_packet, recipient)
            BetterLog.log_packet_sent_bytes(raw_packet)
            return True
        except socket.error as e:
            BetterLog.log_failed_packet_send_bytes(raw_packet, e)
            return False

    def __received_packet__(self, raw_packet: bytes, sender: Tuple[str, int]):
        if not raw_packet:
            BetterLog.log_incoming("Lame Packet")
            return
        packet = Packet.Packet.from_bytes(raw_packet)
        message: Packet.Message | None
        message = self.TRANSACTION_HANDLER.receive_packet(packet, sender)
        if message is not None:
            self.__received_message__(message)

    def send_ack(self, messageid: bytes, recipient: Tuple[str, int]):
        self.send_message(Packet.Message(b'', Packet.PayloadType.ACKNOWLEDGE, 69420, messageid=messageid), recipient,
                          should_track=False)
        self.TRANSACTION_HANDLER.force_close(messageid)

    def __received_message__(self, message: Packet.Message):
        messageid: bytes = message.messageid
        sender: Tuple[str, int] = message.sender
        if message.payloadtype == Packet.PayloadType.CONNECT:
            # CONNECT
            self.send_ack(messageid, sender)

        elif message.payloadtype == Packet.PayloadType.DISCONNECT:
            # DISCONNECT
            self.send_ack(messageid, sender)

        elif message.payloadtype == Packet.PayloadType.HEARTBEAT:
            # HEARTBEAT
            self.send_ack(messageid, sender)

        elif message.payloadtype == Packet.PayloadType.CHAT:
            # CHAT
            self.MESSAGE_LISTENER(message)
            self.send_ack(messageid, sender)
            pass

        elif message.payloadtype == Packet.PayloadType.ACKNOWLEDGE:
            # ACKNOWLEDGE
            self.TRANSACTION_HANDLER.force_close(messageid)

        elif message.payloadtype == Packet.PayloadType.SELECTIVE_REPEAT:
            # SELECTIVE REPEAT
            packets = self.TRANSACTION_HANDLER.recv_selective_repeat(messageid, list(message.payload))
            if packets is not None:
                for p in packets:
                    if p is not None:
                        self.__send_packet__(p, sender)

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")

    def __send_packet__(self, packet: bytes, recipient: Tuple[str, int]) -> bool:
        try:
            asyncio.run_coroutine_threadsafe(self.OUTGOING_QUEUE.put((packet, recipient)), self.OUTGOING_LOOP)
            return True
        except asyncio.QueueFull:
            BetterLog.log_text("OUTGOING QUEUE FULL")
            return False

    def send_message(self, message: Packet.Message, recipient=None, should_track=True) -> bool:
        if recipient is None:
            recipient = (self.HOST, self.PORT)
        sent = []
        for packet in message.to_packet_list():
            bytepacket = packet.to_bytes()
            sent.append(bytepacket)
            if not self.__send_packet__(bytepacket, recipient):
                BetterLog.log_failed_message_send(message)
                return False
        BetterLog.log_message_sent(message)
        if should_track:
            self.TRANSACTION_HANDLER.sent_message(message.messageid, sent, recipient)
        return True

    def shutdown(self):
        self.INCOMING_LOOP.call_soon_threadsafe(self.INCOMING_LOOP.stop)
        self.EXECUTOR.shutdown(wait=True)
        self.SOCKET.close()
        # TODO: Does not handle all of the active threads
