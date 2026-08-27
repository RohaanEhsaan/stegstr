import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

class NostrNIP44:
    """NIP-44 v2 payload wrapper for Stegstr carriers."""
    @staticmethod
    def derive_conversation_key(sender_privkey_hex: str, receiver_pubkey_hex: str) -> bytes:
        # Simplified ECDH key derivation for Nostr
        combined = sender_privkey_hex + receiver_pubkey_hex
        return hashlib.sha256(combined.encode()).digest()

    @staticmethod
    def seal(payload: str, shared_key: bytes) -> bytes:
        chacha = ChaCha20Poly1305(shared_key)
        nonce = os.urandom(12)
        ciphertext = chacha.encrypt(nonce, payload.encode('utf-8'), None)
        return b"\x02" + nonce + ciphertext  # 0x02 indicates NIP-44 v2

    @staticmethod
    def unseal(data: bytes, shared_key: bytes) -> str:
        if data[0] != 2:
            raise ValueError("Unsupported NIP-44 version header")
        nonce = data[1:13]
        ciphertext = data[13:]
        chacha = ChaCha20Poly1305(shared_key)
        return chacha.decrypt(nonce, ciphertext, None).decode('utf-8')