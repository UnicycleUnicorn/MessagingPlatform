from CryptWrapper import CryptWrapper
import time

a = time.time_ns()
s_priv, s_pub = CryptWrapper.generate_dh_keys()
b = time.time_ns()
o_priv, o_pub = CryptWrapper.generate_dh_keys()
c = time.time_ns()
s_aes_gcm = CryptWrapper.generate_aes_gcm_key(s_priv, o_pub)
d = time.time_ns()
o_aes_gcm = CryptWrapper.generate_aes_gcm_key(o_priv, s_pub)
e = time.time_ns()

print(s_pub)
print(o_pub)

message = b'Hello World!'
print(message)
ee = time.time_ns()
ciphertext = CryptWrapper.encrypt(s_aes_gcm, message)
f = time.time_ns()
print(ciphertext)
ff = time.time_ns()
plaintext = CryptWrapper.decrypt(o_aes_gcm, ciphertext)
g = time.time_ns()
print(plaintext)
