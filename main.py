import Server
import Client
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
# COMPLETED: Message IDs
# TODO: Cross-network communication
# COMPLETED: UDP
# TODO: Abstract payload type (to and from bytes)
# TODO: Make MessageReconstructor thread-safe: may be editing items at the same time right now
# TODO: Pull from buffer faster
# TODO: Ensure packet not None

Version = '0.0-0.0'


RUN_AS_SERVER = True
PORT = 8888

if RUN_AS_SERVER:
    server = Server.Server()

    while True:
        message = input()
        if message == "x":
            break

else:
    client = Client.Client("10.127.28.155")

    while True:
        message = input('Enter your message: ')
        if message == "x":
            break

        client.send(message)
