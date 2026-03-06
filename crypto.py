import random
import string

class TianCanCrypto:
    @staticmethod
    def rc4(data: bytes, key: bytes) -> bytes:
        S = list(range(256))
        j = 0
        out = []
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
        i = j = 0
        for char in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            out.append(char ^ S[(S[i] + S[j]) % 256])
        return bytes(out)

    @staticmethod
    def generate_random_key(length=16):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length)).encode()