import asyncio
import json
import time
import hashlib
import os
import websockets

# =====================================================================
# Pure Python secp256k1 & BIP-340 Schnorr Signatures (NIP-01 Compliant)
# Zero external C-extensions required (Works on Python 3.10 through 3.14+)
# =====================================================================

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G_X = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
G_Y = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def _tagged_hash(tag: str, msg: bytes) -> bytes:
    tag_hash = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_hash + tag_hash + msg).digest()

def _point_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and y1 != y2:
        return None
    if x1 == x2:
        m = (3 * x1 * x1) * pow(2 * y1, P - 2, P) % P
    else:
        m = (y2 - y1) * pow(x2 - x1, P - 2, P) % P
    x3 = (m * m - x1 - x2) % P
    y3 = (m * (x1 - x3) - y1) % P
    return (x3, y3)

def _point_mul(p, n):
    r = None
    curr = p
    while n > 0:
        if n & 1:
            r = _point_add(r, curr)
        curr = _point_add(curr, curr)
        n >>= 1
    return r

def _pubkey_from_privkey(d: int):
    p = _point_mul((G_X, G_Y), d)
    return p[0], (p[1] % 2 == 0)

def schnorr_sign(msg: bytes, privkey_bytes: bytes, aux_rand: bytes = None) -> bytes:
    """Computes a BIP-340 64-byte Schnorr signature."""
    d0 = int.from_bytes(privkey_bytes, byteorder="big")
    if not (1 <= d0 <= N - 1):
        raise ValueError("Private key out of valid range")
    
    px, py_is_even = _pubkey_from_privkey(d0)
    d = d0 if py_is_even else N - d0
    
    if aux_rand is None:
        aux_rand = os.urandom(32)
    
    t = d.to_bytes(32, "big")
    t_xor_aux = bytes(a ^ b for a, b in zip(t, _tagged_hash("BIP0340/aux", aux_rand)))
    k0 = int.from_bytes(_tagged_hash("BIP0340/nonce", t_xor_aux + px.to_bytes(32, "big") + msg), "big") % N
    if k0 == 0:
        raise ValueError("Nonce generation produced zero")
    
    rx, ry_is_even = _pubkey_from_privkey(k0)
    k = k0 if ry_is_even else N - k0
    
    e = int.from_bytes(_tagged_hash("BIP0340/challenge", rx.to_bytes(32, "big") + px.to_bytes(32, "big") + msg), "big") % N
    sig = rx.to_bytes(32, "big") + ((k + e * d) % N).to_bytes(32, "big")
    return sig


class NostrRelayClient:
    """
    NIP-01 & strfry compliant Nostr Relay Client.
    Produces valid BIP-340 signatures and queries single-letter tags.
    """
    DEFAULT_RELAYS = [
        "wss://relay.damus.io",
        "wss://nos.lol",
        "wss://relay.nostr.band"
    ]

    def __init__(self, private_key_hex: str = None, relays: list = None):
        self.relays = relays or self.DEFAULT_RELAYS
        if private_key_hex:
            self.privkey_bytes = bytes.fromhex(private_key_hex)
        else:
            self.privkey_bytes = os.urandom(32)
            
        d0 = int.from_bytes(self.privkey_bytes, byteorder="big") % N
        if d0 == 0:
            d0 = 1
            self.privkey_bytes = d0.to_bytes(32, "big")
            
        px, _ = _pubkey_from_privkey(d0)
        self.pubkey_hex = px.to_bytes(32, byteorder="big").hex()

    def _create_and_sign_event(self, kind: int, content: str, tags: list) -> dict:
        created_at = int(time.time())
        # Canonical NIP-01 JSON serialization
        serialized = json.dumps(
            [0, self.pubkey_hex, created_at, kind, tags, content],
            separators=(',', ':'),
            ensure_ascii=False
        )
        event_id = hashlib.sha256(serialized.encode("utf-8")).digest()
        
        # Pure Python BIP-340 Schnorr signature
        sig_bytes = schnorr_sign(event_id, self.privkey_bytes)

        return {
            "id": event_id.hex(),
            "pubkey": self.pubkey_hex,
            "created_at": created_at,
            "kind": kind,
            "tags": tags,
            "content": content,
            "sig": sig_bytes.hex()
        }

    async def publish_carrier_metadata(self, carrier_url: str, file_hash: str, mime: str = "image/jpeg") -> dict:
        """
        Publishes NIP-94 event using single-letter '#t' tags.
        Awaits genuine ['OK', event_id, true] from strfry/relays before reporting success.
        """
        tags = [
            ["url", carrier_url],
            ["m", mime],
            ["x", file_hash],
            ["t", "stegstr"],          # Standard NIP-01 single-letter tag
            ["t", "qim-dct-v1"]
        ]
        
        event = self._create_and_sign_event(kind=1063, content="Stegstr carrier payload", tags=tags)
        successful_relays = []

        for relay in self.relays:
            try:
                async with websockets.connect(relay, ping_timeout=5, close_timeout=5) as ws:
                    await ws.send(json.dumps(["EVENT", event]))
                    resp = await asyncio.wait_for(ws.recv(), timeout=4)
                    parsed = json.loads(resp)
                    # Must receive genuine OK from relay
                    if parsed[0] == "OK" and parsed[1] == event["id"] and parsed[2] is True:
                        successful_relays.append(relay)
            except Exception:
                continue

        if not successful_relays:
            return {
                "status": "error",
                "message": "Event rejected or relays unreachable (0 stored)",
                "accepted_relays": 0
            }

        return {
            "status": "success",
            "event_id": event["id"],
            "accepted_relays": len(successful_relays),
            "relays": successful_relays
        }

    async def discover_carriers(self, limit: int = 20) -> list:
        """Queries single-letter '#t' indexable tag compliant with strfry and NIP-01."""
        subscription_id = f"sub_{int(time.time())}"
        query_filter = {
            "kinds": [1063],
            "#t": ["stegstr"],  # NIP-01 valid filter
            "limit": limit
        }
        
        discovered = []
        for relay in self.relays:
            try:
                async with websockets.connect(relay, ping_timeout=5, close_timeout=5) as ws:
                    await ws.send(json.dumps(["REQ", subscription_id, query_filter]))
                    while True:
                        resp = await asyncio.wait_for(ws.recv(), timeout=3)
                        msg = json.loads(resp)
                        if msg[0] == "EVENT" and msg[1] == subscription_id:
                            discovered.append(msg[2])
                        elif msg[0] == "EOSE":
                            break
            except Exception:
                continue

        return discovered