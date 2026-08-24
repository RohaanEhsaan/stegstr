import argparse
import asyncio
import json
import sys
from engine import StegEngine, calculate_invisibility_metrics
from nostr_sync import NostrSync

def main():
    parser = argparse.ArgumentParser(description="Stegstr CLI & AI Agent Interface")
    parser.add_argument("--mode", choices=["encode", "decode", "sync", "agent-schema"], required=True)
    parser.add_argument("--cover", help="Path to input carrier image")
    parser.add_argument("--output", help="Path to save stego image")
    parser.add_argument("--message", help="Secret message to hide")
    parser.add_argument("--key", default="default-stegstr-key", help="Passphrase key")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON for AI agents")

    args = parser.parse_args()
    engine = StegEngine(key=args.key)

    if args.mode == "encode":
        if not args.cover or not args.output or not args.message:
            sys.exit("Error: --cover, --output, and --message are required for encoding.")
        
        engine.embed(args.cover, args.output, args.message.encode())
        metrics = calculate_invisibility_metrics(args.cover, args.output)
        
        res = {
            "status": "success", 
            "action": "encoded", 
            "file": args.output,
            "metrics": metrics
        }
        if args.json:
            print(json.dumps(res))
        else:
            print(f"Successfully encoded to {args.output}")
            print(f"Invisibility Score: {metrics['psnr_db']} dB ({metrics['invisibility_rating']})")

    elif args.mode == "decode":
        if not args.cover:
            sys.exit("Error: --cover is required for decoding.")
        try:
            msg = engine.extract(args.cover).decode()
            res = {"status": "success", "recovered_message": msg}
            print(json.dumps(res) if args.json else f"Recovered Message: {msg}")
        except Exception as e:
            res = {"status": "error", "message": str(e)}
            print(json.dumps(res) if args.json else f"Decoding Failed: {e}")

    elif args.mode == "sync":
        sync = NostrSync()
        events = asyncio.run(sync.query_steg_events())
        res = {"status": "success", "events_found": len(events), "events": events}
        print(json.dumps(res, indent=2))

    elif args.mode == "agent-schema":
        schema = {
            "name": "stegstr",
            "description": "Steganographic secure transport over Nostr",
            "actions": ["encode", "decode", "sync"]
        }
        print(json.dumps(schema, indent=2))

if __name__ == "__main__":
    main()