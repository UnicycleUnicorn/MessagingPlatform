"""
from CryptWrapper import CryptWrapper


s_priv, s_pub = CryptWrapper.generate_dh_keys()
o_priv, o_pub = CryptWrapper.generate_dh_keys()

s_aes_gcm = CryptWrapper.generate_aes_gcm_key(s_priv, o_pub)
o_aes_gcm = CryptWrapper.generate_aes_gcm_key(o_priv, s_pub)

print(s_pub)
print(o_pub)

message = b'Hello World!'
print(message)
ciphertext = CryptWrapper.encrypt(s_aes_gcm, message)
print(ciphertext)
plaintext = CryptWrapper.decrypt(o_aes_gcm, ciphertext)
print(plaintext)
"""
print(list(b' !"%&\'*,-'))
