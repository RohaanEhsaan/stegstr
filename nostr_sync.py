import asyncio
import json
import time
import websockets

DEFAULT_RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.nostr.band"
]

class NostrSync:
    def __init__(self, relays=None):
        self.relays = relays or DEFAULT_RELAYS

    async def publish_steg_event(self, image_url: str, description: str = "Stegstr Carrier") -> dict:
        """Publishes a NIP-94 File Metadata event referencing the carrier image."""
        event = {
            "kind": 1063,
            "created_at": int(time.time()),
            "tags": [
                ["url", image_url],
                ["m", "image/jpeg"],
                ["steg", "qim-dct-v1"]
            ],
            "content": description
        }
        
        successes = 0
        for relay in self.relays:
            try:
                async with websockets.connect(relay, timeout=5) as ws:
                    await ws.send(json.dumps(["EVENT", event]))
                    successes += 1
            except Exception:
                continue
        return {"status": "broadcast_complete", "relays_reached": successes, "event": event}

    async def query_steg_events(self, limit: int = 10) -> list:
        """Queries relays for recent steganographic carrier events."""
        events = []
        req = ["REQ", "sub_steg", {"kinds": [1063], "#steg": ["qim-dct-v1"], "limit": limit}]
        for relay in self.relays:
            try:
                async with websockets.connect(relay, timeout=5) as ws:
                    await ws.send(json.dumps(req))
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=2)
                        data = json.loads(msg)
                        if data[0] == "EVENT":
                            events.append(data[2])
                        elif data[0] == "EOSE":
                            break
            except Exception:
                continue
        return events