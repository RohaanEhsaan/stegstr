import numpy as np
import scipy.io.wavfile as wav
from reedsolo import RSCodec
import hashlib

class AudioStegEngine:
    def __init__(self, key: str, chip_length: int = 512, gain: float = 0.015):
        """
        DSSS (Direct-Sequence Spread Spectrum) Audio Steganography Engine.
        :param chip_length: Samples per bit (higher = more resilient).
        :param gain: Embedding intensity factor (keeps audio imperceptible).
        """
        self.key = key
        self.chip_length = chip_length
        self.gain = gain
        self.rsc = RSCodec(8)  # 8 parity bytes for error recovery
        self.seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

    def _get_pn_sequence(self, length: int) -> np.ndarray:
        """Generates a bipolar pseudo-random sequence (-1, +1) seeded by the key."""
        np.random.seed(self.seed)
        return np.random.choice([-1.0, 1.0], size=length)

    def embed(self, cover_wav: str, output_wav: str, payload: bytes):
        sr, signal = wav.read(cover_wav)
        is_stereo = signal.ndim > 1
        
        # Work on single channel for carrier signal
        if is_stereo:
            orig_channels = signal.copy()
            carrier = signal[:, 0].astype(np.float32)
        else:
            carrier = signal.astype(np.float32)

        # 1. Protect payload with Reed-Solomon FEC
        fec_data = self.rsc.encode(payload)
        header = len(fec_data).to_bytes(4, byteorder="big")
        total_stream = header + fec_data
        bits = np.unpackbits(np.frombuffer(total_stream, dtype=np.uint8))

        total_samples_needed = len(bits) * self.chip_length
        if total_samples_needed > len(carrier):
            raise ValueError(f"Audio file too short! Need at least {total_samples_needed/sr:.2f}s, got {len(carrier)/sr:.2f}s.")

        # 2. Spread spectrum modulation
        pn = self._get_pn_sequence(self.chip_length)
        max_amp = np.max(np.abs(carrier)) if np.max(np.abs(carrier)) > 0 else 32767.0
        scale = max_amp * self.gain

        stego = carrier.copy()
        for i, bit in enumerate(bits):
            start = i * self.chip_length
            end = start + self.chip_length
            bipolar_bit = 1.0 if bit == 1 else -1.0
            stego[start:end] += bipolar_bit * pn * scale

        # 3. Clip and rebuild channel structure
        stego = np.clip(stego, -32768, 32767).astype(np.int16)
        if is_stereo:
            orig_channels[:, 0] = stego
            final_signal = orig_channels
        else:
            final_signal = stego

        wav.write(output_wav, sr, final_signal)

    def extract(self, stego_wav: str) -> bytes:
        sr, signal = wav.read(stego_wav)
        if signal.ndim > 1:
            carrier = signal[:, 0].astype(np.float32)
        else:
            carrier = signal.astype(np.float32)

        pn = self._get_pn_sequence(self.chip_length)
        total_chips = len(carrier) // self.chip_length

        if total_chips < 32:  # Need at least 4-byte header (32 bits)
            raise ValueError("Audio stream too short to contain header.")

        # Correlate chips to extract raw bits
        extracted_bits = []
        for i in range(total_chips):
            start = i * self.chip_length
            end = start + self.chip_length
            segment = carrier[start:end]
            correlation = np.dot(segment, pn)
            extracted_bits.append(1 if correlation > 0 else 0)

        raw = np.packbits(np.array(extracted_bits, dtype=np.uint8)).tobytes()
        payload_len = int.from_bytes(raw[:4], byteorder="big")

        if payload_len <= 0 or payload_len > (len(raw) - 4):
            raise ValueError("Invalid key or damaged audio carrier.")

        fec_payload = raw[4:4 + payload_len]
        decoded_bytes, _, _ = self.rsc.decode(fec_payload)
        return bytes(decoded_bytes)