import sys
import json
from engine import StegEngine, calculate_invisibility_metrics

MANIFEST = {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "tools": [
        {
            "name": "stegstr_hide",
            "description": "Hides an encrypted message inside an image that survives WhatsApp/Telegram compression.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cover_image": {"type": "string"},
                    "output_image": {"type": "string"},
                    "secret": {"type": "string"},
                    "key": {"type": "string"}
                },
                "required": ["cover_image", "output_image", "secret", "key"]
            }
        },
        {
            "name": "stegstr_reveal",
            "description": "Extracts hidden data from compressed carrier images.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "key": {"type": "string"}
                },
                "required": ["image_path", "key"]
            }
        }
    ]
}

def run_server():
    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        method = req.get("method")
        
        if method == "initialize":
            print(json.dumps({"result": MANIFEST}))
        elif method == "tools/list":
            print(json.dumps({"result": {"tools": MANIFEST["tools"]}}))
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            engine = StegEngine(key=args.get("key", "default"))
            
            if name == "stegstr_hide":
                engine.embed(args["cover_image"], args["output_image"], args["secret"].encode())
                metrics = calculate_invisibility_metrics(args["cover_image"], args["output_image"])
                print(json.dumps({"result": {"content": [{"type": "text", "text": f"Embedded with PSNR {metrics['psnr_db']} dB"}]}}))
            elif name == "stegstr_reveal":
                msg = engine.extract(args["image_path"]).decode(errors="replace")
                print(json.dumps({"result": {"content": [{"type": "text", "text": msg}]}}))
        sys.stdout.flush()

if __name__ == "__main__":
    run_server()