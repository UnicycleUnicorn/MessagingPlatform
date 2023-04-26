import socket

import NetworkCommunicationConstants
import Packet
from typing import Callable, Tuple
import threading
import MessageReconstructor
from concurrent.futures import ThreadPoolExecutor
import BetterLog
import asyncio
from CompletedMessages import CompletedMessages

from OutgoingTracker import OutgoingTracker


class NetworkHandler:
    def __init__(self, port: int, listener: Callable[[Packet.Message], None], host: str = ''):
        # Create an instance of a message reconstructor
        self.MESSAGE_RECONSTRUCTOR = MessageReconstructor.MessageReconstructor()
        self.PORT = port
        self.HOST = host
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SOCKET.bind(('', self.PORT))
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,
                               NetworkCommunicationConstants.OUTGOING_BUFFER_SIZE_BYTES)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,
                               NetworkCommunicationConstants.INCOMING_BUFFER_SIZE_BYTES)

        # Track Completed Messages
        self.COMPLETED_MESSAGES = CompletedMessages(NetworkCommunicationConstants.COMPLETED_MESSAGE_BUFFER_SIZE)

        # Packet status checkers
        self.__incoming_status_checker()
        self.__outgoing_status_checker()
        self.OUTGOING_TRACKER = OutgoingTracker()

        # Set the message listener
        self.MESSAGE_LISTENER = listener

        # Create a thread pool
        self.EXECUTOR = ThreadPoolExecutor(max_workers=6)

        # Create the loop to handle queued items
        self.MESSAGE_QUEUE = asyncio.Queue(maxsize=500)
        self.LOOP = asyncio.new_event_loop()
        t = threading.Thread(target=self.__looper__)
        t.daemon = True
        t.start()

        # Listen for packets
        t = threading.Thread(target=self.__listen__)
        t.daemon = True
        t.start()

    def __looper__(self):
        asyncio.set_event_loop(self.LOOP)
        self.LOOP.create_task(self.__queue_consume__())
        self.LOOP.run_forever()

    def __outgoing_status_checker(self):
        resends = self.OUTGOING_TRACKER.find_resends()
        for resend in resends:
            messageid, packets, recipient = resend
            if self.OUTGOING_TRACKER.resent(messageid, NetworkCommunicationConstants.WAIT_RESPONSE_TIME_NS):
                for packet in packets:
                    self.__send_packet__(packet, recipient)
        status_checker = threading.Timer(NetworkCommunicationConstants.WAIT_RESPONSE_TIME_S, self.__outgoing_status_checker)
        status_checker.start()

    def __incoming_status_checker(self):
        missing_packets = self.MESSAGE_RECONSTRUCTOR.look_for_missing_packets()
        for missing in missing_packets:
            packets, messageid, sender = missing
            if self.MESSAGE_RECONSTRUCTOR.edit_response_time(messageid,
                                                             NetworkCommunicationConstants.WAIT_RESPONSE_TIME_NS):
                message = Packet.Message(bytes(packets), Packet.PayloadType.SELECTIVE_REPEAT, 69420, messageid)
                self.send_message(message, sender)
        status_checker = threading.Timer(NetworkCommunicationConstants.WAIT_TIME_BEFORE_REPEAT_REQUEST_S,
                                         self.__incoming_status_checker)
        status_checker.start()

    def __listen__(self):
        while True:
            asyncio.run_coroutine_threadsafe(
                self.MESSAGE_QUEUE.put(self.SOCKET.recvfrom(NetworkCommunicationConstants.MAXIMUM_PACKET_SIZE_BYTES)),
                self.LOOP)

    async def __queue_consume__(self):
        while True:
            raw_packet, sender = await self.MESSAGE_QUEUE.get()
            self.EXECUTOR.submit(self.__received_packet__, raw_packet, sender)

    def __received_packet__(self, raw_packet: bytes, sender: Tuple[str, int]):
        if not raw_packet:
            BetterLog.log_incoming("Lame Packet")
            return
        packet = Packet.Packet.from_bytes(raw_packet)
        BetterLog.log_packet_received(packet)
        if packet.header.messageid in self.COMPLETED_MESSAGES:
            BetterLog.log_incoming(f"RECEIVED PACKET REGARDING CLOSED MESSAGE: {packet.header.messageid}")
        else:
            message: Packet.Message | None
            message = self.MESSAGE_RECONSTRUCTOR.received_packet(packet, sender)
            if message is not None:
                self.__received_message__(message)

    def send_ack(self, messageid: bytes, recipient: Tuple[str, int]):
        self.send_message(Packet.Message(b'', Packet.PayloadType.ACKNOWLEDGE, 69420, messageid=messageid), recipient,
                          should_track=False)
        self.OUTGOING_TRACKER.close(messageid)

    def __received_message__(self, message: Packet.Message):
        BetterLog.log_message_received(message)
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

        elif message.payloadtype == Packet.PayloadType.ACKNOWLEDGE:
            # ACKNOWLEDGE
            self.OUTGOING_TRACKER.close(messageid)
            self.COMPLETED_MESSAGES.add(messageid)

        elif message.payloadtype == Packet.PayloadType.SELECTIVE_REPEAT:
            # SELECTIVE REPEAT
            packets = self.OUTGOING_TRACKER.get_packets(messageid, list(message.payload))
            if packets is not None:
                for p in packets:
                    self.__send_packet__(p, sender)
                self.OUTGOING_TRACKER.resent(messageid)

        else:
            BetterLog.log_incoming("Received Packet with null Payload Type")

    def __send_packet__(self, packet: bytes, recipient: Tuple[str, int]) -> bool:
        try:
            self.SOCKET.sendto(packet, recipient)
            BetterLog.log_packet_sent_bytes(packet)
            return True
        except socket.error as e:
            BetterLog.log_failed_packet_send_bytes(packet, e)
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
            self.OUTGOING_TRACKER.sent(message.messageid, sent, recipient)
        return True

    def shutdown(self):
        self.LOOP.call_soon_threadsafe(self.LOOP.stop)
        self.EXECUTOR.shutdown(wait=True)
        self.SOCKET.close()
