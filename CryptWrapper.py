import os
from typing import Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.asymmetric.dh import DHPrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class CryptWrapper:
    _dhparam = dh.generate_parameters(generator=2, key_size=2048, backend=default_backend())

    @classmethod
    def generate_dh_keys(cls) -> Tuple[DHPrivateKey, bytes]:
        private = cls._dhparam.generate_private_key()
        return private, private.public_key().public_bytes(encoding=serialization.Encoding.PEM,
                                                          format=serialization.PublicFormat.SubjectPublicKeyInfo)

    @classmethod
    def generate_aes_gcm_key(cls, self_private_dh: DHPrivateKey, other_public_dh: bytes) -> AESGCM:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=None, backend=default_backend())
        received_public_key = serialization.load_pem_public_key(other_public_dh, backend=default_backend())
        shared_key = self_private_dh.exchange(received_public_key)
        aesgcm_key = hkdf.derive(shared_key)
        # TODO: Force overwrite other_public, self_private, shared_key, and aesgcm_key
        return AESGCM(aesgcm_key)

    @classmethod
    def encrypt(cls, aesgcm: AESGCM, plaintext: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + aesgcm.encrypt(nonce, plaintext, None)

    @classmethod
    def decrypt(cls, aesgcm: AESGCM, ciphertext: bytes) -> bytes:
        nonce, ciphertext = ciphertext[:12], ciphertext[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)
