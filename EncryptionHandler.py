from CryptWrapper import CryptWrapper
from cryptography.hazmat.primitives.asymmetric.dh import DHPrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import asyncio
import time
import BetterLog


class AESGCMKeyHasNotBeenGenerated(Exception):
    pass


class EncryptionHandler:
    def __init__(self):
        self.self_prepared = False
        self.other_prepared = False
        self.aes_gcm_shared_key: AESGCM | None = None
        self.dh_public_key = None
        self.dh_private_key = None

    def generate_dh_keys(self):
        self.dh_private_key, self.dh_public_key = CryptWrapper.generate_dh_keys()
        BetterLog.log_text('DH KEYS GENERATED')

    def is_prepared(self):
        return self.self_prepared and self.other_prepared

    def received_other_public_key(self, other_public_key: bytes):
        BetterLog.log_text('OTHER DH KEY RECEIVED')
        while self.dh_private_key is None:
            time.sleep(0.01)

        self.aes_gcm_shared_key = CryptWrapper.generate_aes_gcm_key(self.dh_private_key, other_public_key)
        BetterLog.log_text('AES GCM KEYS GENERATED')
        other_public_key = None
        self.dh_private_key = None
        self.dh_public_key = None

    def encrypt(self, plaintext: bytes) -> bytes:
        if self.aes_gcm_shared_key is None:
            raise AESGCMKeyHasNotBeenGenerated
        return CryptWrapper.encrypt(self.aes_gcm_shared_key, plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        if self.aes_gcm_shared_key is None:
            raise AESGCMKeyHasNotBeenGenerated
        return CryptWrapper.decrypt(self.aes_gcm_shared_key, ciphertext)
