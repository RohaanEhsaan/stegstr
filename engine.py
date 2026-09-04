import hashlib
import cv2
import numpy as np
from reedsolo import RSCodec

MID_COORDS = [(2, 1), (1, 2), (2, 2), (3, 1), (1, 3)]

class StegEngine:
    def __init__(self, key: str = "stegstr-default-key", delta: float = 40.0, target_dim: int = 1080):
        self.key = key
        self.delta = delta
        self.target_dim = target_dim
        self.rsc = RSCodec(16)  # 16 error correction bytes per payload
        self.seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

    def _prepare_payload(self, data: bytes) -> np.ndarray:
        fec_data = self.rsc.encode(data)
        length_header = len(fec_data).to_bytes(4, byteorder="big")
        total_stream = length_header + fec_data
        return np.unpackbits(np.frombuffer(total_stream, dtype=np.uint8))

    def embed(self, cover_path: str, output_path: str, payload: bytes):
        img = cv2.imread(cover_path)
        if img is None:
            raise ValueError(f"Could not load cover image: {cover_path}")

        # Normalize dimensions to survive social resizing
        img = cv2.resize(img, (self.target_dim, self.target_dim), interpolation=cv2.INTER_AREA)

        # Convert to YCrCb (Luminance Y channel handles human visual invariance)
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        y = y.astype(np.float32)

        blocks = self.target_dim // 8
        total_blocks = blocks * blocks
        bits = self._prepare_payload(payload)

        if len(bits) > total_blocks:
            raise ValueError(f"Payload too large: {len(bits)} bits vs {total_blocks} available blocks")

        # Deterministic pseudo-random block selection
        np.random.seed(self.seed)
        shuffled_blocks = np.random.permutation(total_blocks)[:len(bits)]

        for bit_idx, block_id in enumerate(shuffled_blocks):
            by = (block_id // blocks) * 8
            bx = (block_id % blocks) * 8
            
            dct_blk = cv2.dct(y[by:by+8, bx:bx+8])
            bit = bits[bit_idx]

            # QIM modulation across mid-frequency bands
            for u, v in MID_COORDS:
                val = dct_blk[u, v]
                if bit == 1:
                    dct_blk[u, v] = np.round((val - self.delta / 4) / self.delta) * self.delta + self.delta / 4
                else:
                    dct_blk[u, v] = np.round((val + self.delta / 4) / self.delta) * self.delta - self.delta / 4

            y[by:by+8, bx:bx+8] = cv2.idct(dct_blk)

        y = np.clip(y, 0, 255).astype(np.uint8)
        stego_bgr = cv2.cvtColor(cv2.merge([y, cr, cb]), cv2.COLOR_YCrCb2BGR)
        cv2.imwrite(output_path, stego_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])

    def extract(self, stego_path: str) -> bytes:
        img = cv2.imread(stego_path)
        if img is None:
            raise ValueError(f"Could not load stego image: {stego_path}")

        # Resynchronize dimensions if social platform altered aspect/size
        if img.shape[0] != self.target_dim or img.shape[1] != self.target_dim:
            img = cv2.resize(img, (self.target_dim, self.target_dim), interpolation=cv2.INTER_CUBIC)

        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y, _, _ = cv2.split(ycrcb)
        y = y.astype(np.float32)

        blocks = self.target_dim // 8
        total_blocks = blocks * blocks

        np.random.seed(self.seed)
        shuffled_blocks = np.random.permutation(total_blocks)

        extracted_bits = []
        for block_id in shuffled_blocks:
            by = (block_id // blocks) * 8
            bx = (block_id % blocks) * 8
            dct_blk = cv2.dct(y[by:by+8, bx:bx+8])

            votes = [1 if (dct_blk[u, v] % self.delta) < (self.delta / 2) else 0 for u, v in MID_COORDS]
            extracted_bits.append(1 if sum(votes) >= 3 else 0)

        raw = np.packbits(np.array(extracted_bits, dtype=np.uint8)).tobytes()
        payload_len = int.from_bytes(raw[:4], byteorder="big")
        
        if payload_len <= 0 or payload_len > len(raw) - 4:
            raise ValueError("Corrupted carrier or invalid passphrase.")

        fec_payload = raw[4:4 + payload_len]
        decoded = self.rsc.decode(fec_payload)
        decoded_bytes = decoded[0] if isinstance(decoded, tuple) else decoded
        return bytes(decoded_bytes)


def calculate_invisibility_metrics(original_path: str, stego_path: str) -> dict:
    img1 = cv2.imread(original_path)
    img2 = cv2.imread(stego_path)
    
    if img1 is None or img2 is None:
        raise ValueError("Could not load one or both images for metric comparison.")

    # Resize cover to match the stego canvas dimensions to compare steganography, not spatial scaling
    h, w = img2.shape[:2]
    img1_aligned = cv2.resize(img1, (w, h), interpolation=cv2.INTER_AREA)
    
    mse = np.mean((img1_aligned.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        psnr = 100.0
    else:
        psnr = 20 * np.log10(255.0 / np.sqrt(mse))
        
    return {
        "psnr_db": round(psnr, 2),
        "invisibility_rating": "Imperceptible (Passed)" if psnr > 38.0 else "Noticeable Artifacts"
    }