import socket
import Packet
from typing import Callable, Tuple
import threading
import logging


class NetworkHandler:
    def __init__(self, port: int, host: str = ''):
        self.PORT = port
        self.HOST = host
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.HOST == "":
            self.SOCKET.bind((self.HOST, self.PORT))
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.LISTENERS: list[Callable[[Tuple[str, int], Packet.Packet], None]] = []
        threading.Thread(target=self.__listen__).start()

    def __listen__(self):
        while True:
            raw_header, sender = self.SOCKET.recvfrom(Packet.HeaderFormat.TOTAL_LENGTH)
            if not raw_header:
                break
            header = Packet.PacketHeader.from_bytes(raw_header)
            raw_message = b''
            while len(raw_message) < header.messagelength:
                raw_message += self.SOCKET.recvfrom(header.messagelength - len(raw_message))[1]
            threading.Thread(target=self.__received_message__, args=(header, raw_message, sender)).start()

    def __received_message__(self, header: Packet.PacketHeader, raw_message: bytes, sender: Tuple[str, int]):
        packet = Packet.Packet(header, Packet.PacketMessage.from_bytes(raw_message))
        for listener in self.LISTENERS:
            listener(sender, packet)

    def add_listener(self, listener: Callable[[Tuple[str, int], Packet.Packet], None]):
        self.LISTENERS.append(listener)

    def send(self, packet: Packet.Packet, recipient=None) -> bool:
        if recipient is None:
            recipient = (self.HOST, self.PORT)
        try:
            with self.SOCKET as sock:
                sock.sendto(packet.to_bytes(), recipient)
                return True
        except socket.error as e:
            logging.info(f"Failed to send packet: {e}")
            return False


""" UDP SERVER
import socket

HOST = ''  # Listen on all available interfaces
PORT = 12345

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to a specific address and port
server_socket.bind((HOST, PORT))

while True:
    # Receive data from client
    data, client_address = server_socket.recvfrom(1024)

    # Process the data
    print(f"Received data from {client_address}: {data.decode()}")

    # Send a response back to the client
    server_socket.sendto(b"Response message", client_address)
"""

""" UDP CLIENT
import socket

HOST = '10.0.0.33'  # Replace with your friend's IP address
PORT = 12345

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    # Get input from user
    message = input("Enter message: ")

    # Send message to server
    client_socket.sendto(message.encode(), (HOST, PORT))
    
    # Receive response from server
    response, server_address = client_socket.recvfrom(1024)

    # Process the response
    print(f"Received response from {server_address}: {response.decode()}")
"""
