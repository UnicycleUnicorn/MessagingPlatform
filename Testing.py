
from CryptWrapper import CryptWrapper

dh_private, dh_public = CryptWrapper.generate_dh_keys()
print(dh_public)
other_dh_public = bytes(input("Enter other public: "), "utf-8")

s_aes_gcm = CryptWrapper.generate_aes_gcm_key(dh_private, other_dh_public)
print("AES GCM KEYS GENERATED")

