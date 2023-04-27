def ms_to_ns(ms): return int(ms * 1_000_000)


def s_to_ns(s): return int(s * 1_000_000_000)


def ns_to_s(ns): return float(ns / 1_000_000_000)


MAXIMUM_PACKET_SIZE_BYTES: int = 982
''' Maximum packet size (bytes) sent by our protocol, keep in mind that this does not include UDP headers '''

HEARTBEAT_FREQUENCY_NS: int = 0
''' Frequency (ns) of heartbeats sent by client to server '''

HEARTBEAT_TIMEOUT_NS: int = 0
''' Timeout (ns) of a client after not receiving a heartbeat '''

OUTGOING_BUFFER_SIZE_BYTES: int = 16_384
''' Size (bytes) of the output / send buffer '''

INCOMING_BUFFER_SIZE_BYTES: int = 16_384
''' Size (bytes) of the input / receive buffer '''

COMPLETED_MESSAGE_BUFFER_SIZE: int = 1000
''' Size (count) of the buffer that stores id's of previously completed communications '''

WAIT_TIME_BEFORE_REPEAT_REQUEST_NS: int = 50_000_000
''' Time (ns) waited after most recent packet before asking for a repeat '''
WAIT_TIME_BEFORE_REPEAT_REQUEST_S: float = ns_to_s(WAIT_TIME_BEFORE_REPEAT_REQUEST_NS)

WAIT_RESPONSE_TIME_NS: int = 75_000_000
''' Time (ns) waited for response before resending a message '''
WAIT_RESPONSE_TIME_S: float = ns_to_s(WAIT_RESPONSE_TIME_NS)

GIVE_UP_REATTEMPTS: int = 3
''' Attempts before giving up (int) '''

FIND_RESEND_REPEAT_FAIL_POLL_TIME_NS: int = 25_000_000
''' Time (ns) between polls for resend, repeats, and failed messages'''
FIND_RESEND_REPEAT_FAIL_POLL_TIME_S = ns_to_s(FIND_RESEND_REPEAT_FAIL_POLL_TIME_NS)
