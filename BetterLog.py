import threading

import eel

from Packet import Packet, Message

PRETTY_PRINT = False
CALLBACK = None


@eel.expose
def log_text(text: str):
    if not PRETTY_PRINT:
        # Call a JavaScript function to add the message to the log
        eel.add_log_message(text)


@eel.expose
def log_outgoing(text: str):
    if not PRETTY_PRINT:
        # Call a JavaScript function to add the message to the log
        eel.add_outgoing_message(text)


@eel.expose
def log_incoming(text: str):
    if not PRETTY_PRINT:
        # Call a JavaScript function to add the message to the log
        eel.add_incoming_message(text)


@eel.expose
def log_message_text(text: str, sender: str, isself: bool = False):
    if PRETTY_PRINT:
        eel.add_message_text(text, sender, isself)


@eel.expose
def submit_message(text):
    try:
        CALLBACK(text)
    except:
        log_text('MESSAGE COULD NOT BE SENT')


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


def log_packet_sent_bytes(packet: bytes):
    log_packet_sent(Packet.from_bytes(packet))


def log_failed_packet_send_bytes(packet: bytes, e: Exception):
    log_failed_packet_send(Packet.from_bytes(packet), e)


def log_failed_message_send(message: Message):
    log_outgoing(f"FAILED TO SEND\n{message.__str__()}")


def log_failed_packet_send(packet: Packet, e: Exception):
    log_outgoing(f"FAILED TO SEND\n{packet.__str__()}\n{e}")
