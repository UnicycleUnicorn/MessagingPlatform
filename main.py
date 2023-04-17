import Server
import Client
import logging
import socket

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
print(f"Hostname: {hostname}")
print(f"IP Address: {ip_address}")

# TODO: tor / i2p
# TODO: GUI
# TODO: Server handles multiple clients and broadcasts messages
# TODO: Message encryption
# COMPLETED: Handle different sized messages
# TODO: Try using different ports
# TODO: Send images
# TODO: Use markdown for text formatting
# TODO: Different message types
# TODO: Version Checking
# TODO: Message IDs
# TODO: Cross-network communication
# TODO: UDP
# TODO: Daemon threads instead
# TODO: Abstract payload type (to and from bytes)

Version = '0.0-0.0'

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)

RUN_AS_SERVER = True

if RUN_AS_SERVER:
    server = Server.Server(8888)

    # Loop to receive and send_packet messages
    while True:
        # Send message to client
        message = input('Enter x to quit:')
        if message == "x":
            break

else:
    client = Client.Client(8888, "10.127.28.155")

    # Loop to receive and send_packet messages
    while True:
        # Send message to client
        message = input('Enter your message: ')
        if message == "x":
            break

        client.send(message)
