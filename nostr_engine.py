import base64
import hashlib
import json
import time
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os

class NostrCrypto:
    @staticmethod
    def encrypt_payload(plaintext: str, secret_key: str) -> bytes:
        """Encrypts data using ChaCha20-Poly1305 derived from the shared key."""
        key_bytes = hashlib.sha256(secret_key.encode()).digest()
        chacha = ChaCha20Poly1305(key_bytes)
        nonce = os.urandom(12)
        ciphertext = chacha.encrypt(nonce, plaintext.encode('utf-8'), None)
        # Store as nonce (12 bytes) + ciphertext
        return nonce + ciphertext

    @staticmethod
    def decrypt_payload(raw_encrypted: bytes, secret_key: str) -> str:
        """Decrypts ChaCha20-Poly1305 encrypted payload."""
        key_bytes = hashlib.sha256(secret_key.encode()).digest()
        chacha = ChaCha20Poly1305(key_bytes)
        nonce = raw_encrypted[:12]
        ciphertext = raw_encrypted[12:]
        decrypted = chacha.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')