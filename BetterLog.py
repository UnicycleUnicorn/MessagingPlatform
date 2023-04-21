import eel
import threading
from Packet import Packet, Message


@eel.expose
def log_text(text: str):
    # Call a JavaScript function to add the message to the log
    eel.add_log_message(text)


@eel.expose
def log_outgoing(text: str):
    # Call a JavaScript function to add the message to the log
    eel.add_outgoing_message(text)


@eel.expose
def log_incoming(text: str):
    # Call a JavaScript function to add the message to the log
    eel.add_incoming_message(text)


# Initialize Eel with your HTML file
eel.init('web')

# Start the Eel application
thread = threading.Thread(target=eel.start, args=('log.html',))
thread.daemon = True
thread.start()


def log_packet_received(packet: Packet):
    log_incoming(packet.__str__())


def log_message_received(message: Message):
    log_incoming(message.__str__())


def log_packet_sent(packet: Packet):
    log_outgoing(packet.__str__())


def log_message_sent(message: Message):
    log_outgoing(message.__str__())


def log_failed_message_send(message: Message):
    log_outgoing(f"FAILED TO SEND\n{message.__str__()}")


def log_failed_packet_send(packet: Packet, e: Exception):
    log_outgoing(f"FAILED TO SEND\n{packet.__str__()}\n{e}")
