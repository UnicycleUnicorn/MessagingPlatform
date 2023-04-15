import multiprocessing
import Server
import Client
import logging

multiprocessing.freeze_support()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)

RUN_AS = 'server'

if RUN_AS == 'server':
    server = Server.Server()

    # Loop to receive and send messages
    while True:
        # Send message to client
        message = input('Enter your message: ')
        if message == "x":
            break
        server.send(message)

    del server

elif RUN_AS == 'client':
    client = Client.Client("10.127.28.65")

    # Loop to receive and send messages
    while True:
        # Send message to client
        message = input('Enter your message: ')
        if message == "x":
            break
        client.send(message)

    del client
