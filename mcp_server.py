import asyncio
import json
import sys
from engine import StegEngine
from nostr_engine import NostrCrypto

# Protocol Definition for LLM Tool Calling / MCP
TOOLS_MANIFEST = {
    "tools": [
        {
            "name": "stegstr_encode",
            "description": "Invisibly hides an encrypted Nostr message inside an image that survives social media recompression.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cover_path": {"type": "string", "description": "Local path to carrier image"},
                    "output_path": {"type": "string", "description": "Output path for stego image"},
                    "message": {"type": "string", "description": "Message or Nostr event content to hide"},
                    "passphrase": {"type": "string", "description": "Encryption key"}
                },
                "required": ["cover_path", "output_path", "message", "passphrase"]
            }
        },
        {
            "name": "stegstr_decode",
            "description": "Extracts and decrypts a hidden message from a carrier image.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "Path to stego image"},
                    "passphrase": {"type": "string", "description": "Decryption key"}
                },
                "required": ["image_path", "passphrase"]
            }
        }
    ]
}

def handle_agent_call(tool_name: str, args: dict):
    passphrase = args.get("passphrase", "default-key")
    engine = StegEngine(key=passphrase)
    
    if tool_name == "stegstr_encode":
        encrypted_bytes = NostrCrypto.encrypt_payload(args["message"], passphrase)
        engine.embed(args["cover_path"], args["output_path"], encrypted_bytes)
        return {"status": "success", "output_file": args["output_path"]}
        
    elif tool_name == "stegstr_decode":
        raw_bytes = engine.extract(args["image_path"])
        decrypted_msg = NostrCrypto.decrypt_payload(raw_bytes, passphrase)
        return {"status": "success", "message": decrypted_msg}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manifest":
        print(json.dumps(TOOLS_MANIFEST, indent=2))
    else:
        # Simple stdio execution loop for agent pipelines
        for line in sys.stdin:
            if not line.strip(): continue
            req = json.loads(line)
            result = handle_agent_call(req.get("tool"), req.get("arguments", {}))
            print(json.dumps(result))
            sys.stdout.flush()