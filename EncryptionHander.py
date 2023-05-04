from CryptWrapper import CryptWrapper
from cryptography.hazmat.primitives.asymmetric.dh import DHPrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AESGCMKeyHasNotBeenGenerated(Exception):
    pass


class EncryptionHandler:
    def __init__(self):
        self.dh_private_key: DHPrivateKey | None = None
        self.dh_public_key: bytes | None = None
        self.aes_gcm_shared_key: AESGCM | None = None
        self.dh_private_key, self.dh_public_key = CryptWrapper.generate_dh_keys()

    def received_other_public_key(self, other_public_key: bytes):
        pass

    def encrypt(self, plaintext: bytes) -> bytes:
        if self.aes_gcm_shared_key is None:
            raise AESGCMKeyHasNotBeenGenerated
        return CryptWrapper.encrypt(self.aes_gcm_shared_key, plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        if self.aes_gcm_shared_key is None:
            raise AESGCMKeyHasNotBeenGenerated
        return CryptWrapper.decrypt(self.aes_gcm_shared_key, ciphertext)
