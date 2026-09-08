# Stegstr — Resilient Steganography & Nostr Carrier Engine

[![Contest Result](https://img.shields.io/badge/Stegstr_Gauntlet-100%25_Blind_Survival-success)](#)
[![Invisibility](https://img.shields.io/badge/PSNR-50.1_dB_(Contest_Record)-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

A high-fidelity, lossy-compression-resilient steganographic codec built for covert data transport across social platforms and decentralized networks like Nostr. 

Developed for the **Stegstr Contest (Entry #101)**, this implementation achieved **100% blind survival** across all standard lossy profiles while setting the contest record for visual fidelity at **50.1 dB PSNR**.

---

## Key Features

* **High-Fidelity QIM-DCT Engine:** Calibrated mid-frequency Discrete Cosine Transform (DCT) Quantization Index Modulation combined with Reed-Solomon error correction (`RSCodec(16)`).
* **Compression Resilience:** Survives aggressive real-world lossy compression pipelines, including WhatsApp (adaptive 1600px, Q=70), Instagram (1080px, Q=75), and Telegram (Q=65).
* **Pure-Python BIP-340 Schnorr Signing:** Native secp256k1 elliptic curve implementation generating valid 64-byte Schnorr signatures and 32-byte public keys without compiled C dependencies.
* **NIP-01 Compliant Nostr Sync:** WebSockets client adhering to NIP-01 event schemas, relay verification (`["OK", event_id, true]`), and standardized `#t` single-letter tag indexing for strict relays like `strfry`.

---

## Quick Start

### 1. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/RohaanEhsaan/stegstr.git
cd stegstr
pip install -r requirements.txt
```
### 2. Run the Web Interface
Launch the interactive Streamlit dashboard:

```bash
streamlit run app.py
```
### 3. Run the Survival Test Suite
Verify 100% payload recovery against real-world social compression profiles:

```bash
python test_survival.py
```
### 4. Verify BIP-340 Nostr Event Signing
Generate and verify a cryptographically signed NIP-01 event directly in the terminal:

```bash
python -c "from nostr_sync import NostrRelayClient; c = NostrRelayClient(); ev = c._create_and_sign_event(1063, 'test_payload', [['t', 'stegstr']]); print('Signed Event ID:', ev['id']); print('BIP-340 Sig:', ev['sig']); print('Pubkey:', ev['pubkey'])"
```
## Official Contest Recognition

> *"A lean Python codec with the best invisibility among the 100% survivors; audio steganography experiments."*  
> — **Official Stegstr Contest Finalist Record** ([stegstr.com](https://stegstr.com))

---

## Benchmark Results (Independent Gauntlet Audit)

| Metric | Result | Benchmark Context |
| :--- | :--- | :--- |
| **Blind Gauntlet Survival** | **100%** | Unaltered payload recovery across 5 blind lossy compression profiles |
| **Invisibility (PSNR)** | **50.1 dB** | Highest visual fidelity score in the competition field (119 entries) |
| **Cover Robustness** | **93% Mean** | 100% on gradients, 100% on textures, 80% on high-entropy covers |
| **Social Pipelines** | **Passed** | 100% data recovery on simulated WhatsApp, Telegram, and Instagram |
---

## License

Distributed under the MIT License. See `LICENSE` for more information.
