import time
from typing import Tuple, Dict, List

import BetterLog
from EncryptionHandler import EncryptionHandler
import NetworkCommunicationConstants


class ConnectedClient:
    def __init__(self, user_id: int, payload: bytes):
        self.user_id = user_id
        self.should_hear_from_time = 0
        self.heard_from()
        self.encryption_handler = EncryptionHandler(payload)

    def heard_from(self):
        self.should_hear_from_time = time.time_ns() + NetworkCommunicationConstants.HEARTBEAT_TIMEOUT_NS

    def has_heard_from_recently(self, current_time_ns: int) -> bool:
        return self.should_hear_from_time > current_time_ns


class ClientList:
    def __init__(self):
        self.client_dictionary: Dict[Tuple[str, int], ConnectedClient] = {}

    def received_connection(self, client: Tuple[str, int], user_id: int | None, payload: bytes):
        BetterLog.log_text(f"ADDED NEW CLIENT: {client}")
        self.client_dictionary[client] = ConnectedClient(user_id, payload)

    def received_heartbeat(self, client: Tuple[str, int]):
        if client in self.client_dictionary:
            BetterLog.log_text(f"RECEIVED HEARTBEAT: {client}")
            self.client_dictionary[client].heard_from()
        else:
            self.received_connection(client, None)

    def force_disconnect(self, client: Tuple[str, int]):
        BetterLog.log_text(f"DISCONNECTING CLIENT: {client}")
        self.client_dictionary.pop(client, None)

    def disconnect_inactive(self) -> List[Tuple[str, int]]:
        current = time.time_ns()
        disconnecting: List[Tuple[str, int]] = []
        for client, connected_client in self.client_dictionary.items():
            if not connected_client.has_heard_from_recently(current):
                disconnecting.append(client)

        for dis in disconnecting:
            self.force_disconnect(dis)

        return disconnecting

    def __iter__(self):
        return iter(self.client_dictionary.items())
