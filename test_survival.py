import cv2
import os
import numpy as np
from engine import StegEngine

def simulate_platforms(input_stego: str):
    img = cv2.imread(input_stego)
    
    # 1. Simulate WhatsApp: Downscale to max 1600px + aggressive JPEG recompression (Q=70)
    h, w = img.shape[:2]
    scale = min(1.0, 1600 / max(h, w))
    wa = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    cv2.imwrite("test_whatsapp.jpg", wa, [cv2.IMWRITE_JPEG_QUALITY, 70])

    # 2. Simulate Instagram: 1080px square + JPEG Q=75
    insta = cv2.resize(img, (1080, 1080), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite("test_instagram.jpg", insta, [cv2.IMWRITE_JPEG_QUALITY, 75])

    # 3. Simulate Telegram: Standard lossy JPEG Q=65
    cv2.imwrite("test_telegram.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 65])

if __name__ == "__main__":
    engine = StegEngine(key="contest-winning-key")
    test_msg = b"NOSTR_PAYLOAD:npub180cvv07tjdrrgpa0j7j7tmn022..._SURVIVED"

    # Create dummy carrier image (adds subtle noise texture so compression acts naturally)
    np.random.seed(42)
    dummy = np.random.randint(80, 180, (1080, 1080, 3), dtype=np.uint8)
    cv2.imwrite("cover_base.jpg", dummy)

    print("[1] Embedding payload...")
    engine.embed("cover_base.jpg", "stego_initial.jpg", test_msg)

    print("[2] Simulating platform compression (WhatsApp, Telegram, Instagram)...")
    simulate_platforms("stego_initial.jpg")

    print("[3] Testing extraction from compressed platforms:")
    for platform_file in ["test_whatsapp.jpg", "test_instagram.jpg", "test_telegram.jpg"]:
        try:
            recovered = engine.extract(platform_file)
            assert recovered == test_msg
            print(f"  ✓ {platform_file}: PASSED (100% data recovered)")
        except Exception as e:
            print(f"  ✗ {platform_file}: FAILED ({e})")