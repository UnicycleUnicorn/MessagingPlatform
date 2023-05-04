import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import BetterLog
from CryptWrapper import CryptWrapper


class AESGCMKeyHasNotBeenGenerated(Exception):
    pass


class EncryptionHandler:
    def __init__(self, dh_parameters: bytes | None):
        self.self_prepared = False
        self.other_prepared = False
        self.aes_gcm_shared_key: AESGCM | None = None
        self.dh_public_key = None
        self.dh_private_key = None
        if dh_parameters is None:
            self.dh_parameters = dh.generate_parameters(generator=2, key_size=2048, backend=default_backend())
            self.dh_parameters_bytes = self.dh_parameters.parameter_bytes(encoding=serialization.Encoding.PEM, format=serialization.ParameterFormat.PKCS3)
        else:
            self.dh_parameters_bytes = dh_parameters
            self.dh_parameters = serialization.load_pem_parameters(dh_parameters, backend=default_backend())

    def generate_dh_keys(self) -> bytes:
        BetterLog.log_text('GENERATING DH KEYS')
        self.dh_private_key, self.dh_public_key = CryptWrapper.generate_dh_keys(self.dh_parameters)
        BetterLog.log_text('DH KEYS GENERATED')
        return self.dh_public_key

    def is_prepared(self):
        return self.self_prepared and self.other_prepared

    def received_other_public_key(self, other_public_key: bytes):
        BetterLog.log_text('OTHER DH KEY RECEIVED')
        while self.dh_private_key is None:
            time.sleep(0.01)
        BetterLog.log_text('GENERATING AES GCM KEYS')
        self.aes_gcm_shared_key = CryptWrapper.generate_aes_gcm_key(self.dh_private_key, other_public_key)
        BetterLog.log_text('AES GCM KEYS GENERATED')
        other_public_key = None
        self.dh_private_key = None
        self.dh_public_key = None
        self.dh_parameters_bytes = None
        self.dh_parameters = None

    def encrypt(self, plaintext: bytes) -> bytes:
        if self.aes_gcm_shared_key is None:
            raise AESGCMKeyHasNotBeenGenerated
        return CryptWrapper.encrypt(self.aes_gcm_shared_key, plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        if self.aes_gcm_shared_key is None:
            raise AESGCMKeyHasNotBeenGenerated
        return CryptWrapper.decrypt(self.aes_gcm_shared_key, ciphertext)
