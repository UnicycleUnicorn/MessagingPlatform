import logging
import socket
import time

import Packet
from typing import Callable, Tuple
import threading
import MessageReconstructor
from concurrent.futures import ThreadPoolExecutor
import logwrapper
import asyncio


class NetworkHandler:
    def __init__(self, port: int, listener: Callable[[Packet.Message], None], host: str = ''):
        # Create an instance of a message reconstructor
        self.MESSAGE_RECONSTRUCTOR = MessageReconstructor.MessageReconstructor()
        self.PORT = port
        self.HOST = host
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SOCKET.bind(('', self.PORT))
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16384)
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16384)

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

    def __listen__(self):
        while True:
            asyncio.run_coroutine_threadsafe(self.MESSAGE_QUEUE.put(self.SOCKET.recvfrom(Packet.Packet.MAX_PACKET_SIZE)), self.LOOP)

    async def __queue_consume__(self):
        while True:
            raw_packet, sender = await self.MESSAGE_QUEUE.get()
            self.EXECUTOR.submit(self.__received_packet__, raw_packet, sender)

    def __received_packet__(self, raw_packet: bytes, sender: Tuple[str, int]):
        if not raw_packet:
            logging.warning("Lame Packet")
            return
        packet = Packet.Packet.from_bytes(raw_packet)
        logwrapper.received_packet(packet)
        message: Packet.Message | None
        message = self.MESSAGE_RECONSTRUCTOR.received_packet(packet, sender)
        if message is not None:
            logwrapper.received_message(message)
            self.MESSAGE_LISTENER(message)

    def __send_packet__(self, packet: Packet.Packet, recipient=None) -> bool:
        if recipient is None:
            recipient = (self.HOST, self.PORT)
        try:
            self.SOCKET.sendto(packet.to_bytes(), recipient)
            logwrapper.sent_packet(packet)
            return True
        except socket.error as e:
            logwrapper.failed_to_send_packet(packet, e)
            return False

    def send_message(self, message: Packet.Message, recipient=None):
        for packet in message.to_packet_list():
            if not self.__send_packet__(packet, recipient):
                logwrapper.failed_to_send_message(message)
                return False
            time.sleep(0.01)
        logwrapper.sent_message(message)
        return True

    def shutdown(self):
        self.LOOP.call_soon_threadsafe(self.LOOP.stop)
        self.EXECUTOR.shutdown(wait=True)
        self.SOCKET.close()
