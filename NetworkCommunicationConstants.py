def ms_to_ns(ms): return int(ms * 1000000)


def s_to_ns(s): return int(s * 1000000000)


def ns_to_s(ns): return float(ns / 1000000000)


MAXIMUM_PACKET_SIZE_BYTES: int = 0
''' Maximum packet size (bytes) sent by our protocol, keep in mind that this does not include UDP headers '''

HEARTBEAT_FREQUENCY_NS: int = 0
''' Frequency (ns) of heartbeats sent by client to server '''

HEARTBEAT_TIMEOUT_NS: int = 0
''' Timeout (ns) of a client after not receiving a heartbeat '''

OUTGOING_BUFFER_SIZE_BYTES: int = 0
''' Size (bytes) of the output / send buffer '''

INCOMING_BUFFER_SIZE_BYTES: int = 0
''' Size (bytes) of the input / receive buffer '''

COMPLETED_MESSAGE_BUFFER_SIZE: int = 0
''' Size (count) of the buffer that stores id's of previously completed communications '''

WAIT_TIME_BEFORE_REPEAT_NS: int = 0
''' Time (ns) waited after more recent packet before asking for a repeat '''

WAIT_RESPONSE_TIME_NS: int = 0
''' Time (ns) waited for response before resending a message '''
