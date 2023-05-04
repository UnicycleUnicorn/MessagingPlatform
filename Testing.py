"""
from CryptWrapper import CryptWrapper

dh_private, dh_public = CryptWrapper.generate_dh_keys()
print(dh_public)
other_dh_public = bytes(input("Enter other public: "), "utf-8")

s_aes_gcm = CryptWrapper.generate_aes_gcm_key(dh_private, other_dh_public)
print("AES GCM KEYS GENERATED")
"""

from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Generate DH parameters
parameters = dh.generate_parameters(generator=2, key_size=2048, backend=default_backend())

# Serialize the parameters
serialized_params = parameters.parameter_bytes(encoding=serialization.Encoding.PEM, format=serialization.ParameterFormat.PKCS3)

with open('dh_params.pem', 'wb') as f:
    f.write(serialized_params)
