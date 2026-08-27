import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from engine import StegEngine, calculate_invisibility_metrics
from audio_engine import AudioStegEngine

st.set_page_config(page_title="Stegstr - Nostr Steganography", page_icon="🔒", layout="wide")

st.title("🔒 Stegstr: Robust Nostr Steganography")
st.markdown("FOSS multi-modal steganography engine resilient to social media recompression (WhatsApp, Telegram, Instagram) and built for Nostr.")

engine_key = st.sidebar.text_input("Encryption Key / Passphrase", value="contest-winning-key", type="password")
engine = StegEngine(key=engine_key)
audio_engine = AudioStegEngine(key=engine_key)

tab1, tab2, tab3, tab4 = st.tabs([
    "🖼️ Image Encode", 
    "🔍 Image Decode", 
    "🎙️ Audio Steganography", 
    "⚡ Platform Stress-Test"
])

# ---------------------------------------------------------
# Tab 1: Image Encode
# ---------------------------------------------------------
with tab1:
    st.header("1. Encode Hidden Message (Image)")
    col1, col2 = st.columns(2)
    with col1:
        uploaded_cover = st.file_uploader("Upload Carrier Image (JPG/PNG)", type=["jpg", "jpeg", "png"], key="enc_up")
        secret_payload = st.text_area("Secret Message / Nostr Note", height=120, key="img_payload")
    
    with col2:
        if uploaded_cover and secret_payload:
            if st.button("Encode into Carrier Image"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_in, \
                     tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_out:
                    tmp_in.write(uploaded_cover.read())
                    tmp_in_path = tmp_in.name
                    tmp_out_path = tmp_out.name

                try:
                    engine.embed(tmp_in_path, tmp_out_path, secret_payload.encode())
                    metrics = calculate_invisibility_metrics(tmp_in_path, tmp_out_path)
                    
                    st.success("Message successfully embedded!")
                    st.metric(
                        label="Steganographic Invisibility (PSNR)", 
                        value=f"{metrics['psnr_db']} dB", 
                        delta=metrics["invisibility_rating"]
                    )
                    
                    st.image(tmp_out_path, caption=f"Encoded Carrier (PSNR: {metrics['psnr_db']} dB)", use_container_width=True)
                    with open(tmp_out_path, "rb") as f:
                        st.download_button("Download Stego Image", f.read(), file_name="stegstr_carrier.jpg", mime="image/jpeg")
                except Exception as e:
                    st.error(f"Encoding error: {e}")
                finally:
                    if os.path.exists(tmp_in_path): os.remove(tmp_in_path)
                    if os.path.exists(tmp_out_path): os.remove(tmp_out_path)

# ---------------------------------------------------------
# Tab 2: Image Decode
# ---------------------------------------------------------
with tab2:
    st.header("2. Decode & Recover Payload (Image)")
    uploaded_stego = st.file_uploader("Upload Image to Extract Secret From", type=["jpg", "jpeg", "png"], key="dec_up")
    if uploaded_stego:
        if st.button("Extract Hidden Message from Image"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_dec:
                tmp_dec.write(uploaded_stego.read())
                tmp_dec_path = tmp_dec.name

            try:
                extracted_bytes = engine.extract(tmp_dec_path)
                st.success("Extraction Successful!")
                st.code(extracted_bytes.decode(errors="replace"), language="text")
            except Exception as e:
                st.error(f"Extraction failed: {e}. Check passphrase or image integrity.")
            finally:
                if os.path.exists(tmp_dec_path): os.remove(tmp_dec_path)

# ---------------------------------------------------------
# Tab 3: Audio Steganography (WAV)
# ---------------------------------------------------------
with tab3:
    st.header("3. Audio Steganography (Echo Hiding & Phase Modulation)")
    st.caption("Embeds and extracts resilient data within uncompressed/compressed audio streams.")
    
    audio_mode = st.radio("Select Action", ["Encode into Audio", "Decode from Audio"], horizontal=True)
    
    if audio_mode == "Encode into Audio":
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            uploaded_wav = st.file_uploader("Upload Carrier Audio (WAV format)", type=["wav"], key="wav_enc_up")
            audio_secret = st.text_area("Secret Audio Payload", height=100, key="audio_payload_input")
        
        with col_a2:
            if uploaded_wav and audio_secret:
                if st.button("Embed Message into Audio"):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav_in, \
                         tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav_out:
                        tmp_wav_in.write(uploaded_wav.read())
                        tmp_wav_in_path = tmp_wav_in.name
                        tmp_wav_out_path = tmp_wav_out.name

                    try:
                        audio_engine.embed(tmp_wav_in_path, tmp_wav_out_path, audio_secret.encode())
                        st.success("Payload successfully embedded in audio track!")
                        st.audio(tmp_wav_out_path, format="audio/wav")
                        
                        with open(tmp_wav_out_path, "rb") as f:
                            st.download_button("Download Stego WAV", f.read(), file_name="stegstr_audio.wav", mime="audio/wav")
                    except Exception as e:
                        st.error(f"Audio encoding error: {e}")
                    finally:
                        if os.path.exists(tmp_wav_in_path): os.remove(tmp_wav_in_path)
                        if os.path.exists(tmp_wav_out_path): os.remove(tmp_wav_out_path)
                        
    else:
        uploaded_stego_wav = st.file_uploader("Upload Stego Audio to Decode (WAV)", type=["wav"], key="wav_dec_up")
        if uploaded_stego_wav:
            if st.button("Extract Hidden Message from Audio"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav_dec:
                    tmp_wav_dec.write(uploaded_stego_wav.read())
                    tmp_wav_dec_path = tmp_wav_dec.name

                try:
                    recovered_audio_bytes = audio_engine.extract(tmp_wav_dec_path)
                    st.success("Audio Extraction Successful!")
                    st.code(recovered_audio_bytes.decode(errors="replace"), language="text")
                except Exception as e:
                    st.error(f"Audio decoding failed: {e}. Check key or audio duration.")
                finally:
                    if os.path.exists(tmp_wav_dec_path): os.remove(tmp_wav_dec_path)

# ---------------------------------------------------------
# Tab 4: Platform Stress-Test
# ---------------------------------------------------------
with tab4:
    st.header("4. Social Platform Survival Simulator")
    st.info("Simulates real-world lossy compression pipelines (aggressive downscaling + low-quality JPEG re-encoding).")
    test_img = st.file_uploader("Upload Image for Multi-Platform Stress Test", type=["jpg", "jpeg", "png"], key="stress_up")
    stress_msg = st.text_input("Stress Test Payload", value="Testing Nostr survivability across WhatsApp/Telegram/Instagram")
    
    if test_img and st.button("Run Simulation Suite"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_cov, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_enc:
            tmp_cov.write(test_img.read())
            tmp_cov_path = tmp_cov.name
            tmp_enc_path = tmp_enc.name

        try:
            engine.embed(tmp_cov_path, tmp_enc_path, stress_msg.encode())
            img_mat = cv2.imread(tmp_enc_path)
            
            platforms = {
                "WhatsApp (Max 1600px, Q=70)": (1600, 70),
                "Instagram (1080px Square, Q=75)": (1080, 75),
                "Telegram (Standard Lossy Q=65)": (1080, 65)
            }
            
            cols = st.columns(3)
            for idx, (pname, (dim, q)) in enumerate(platforms.items()):
                with cols[idx]:
                    st.subheader(pname)
                    p_path = f"sim_{idx}.jpg"
                    resized = cv2.resize(img_mat, (dim, dim), interpolation=cv2.INTER_AREA)
                    cv2.imwrite(p_path, resized, [cv2.IMWRITE_JPEG_QUALITY, q])
                    
                    try:
                        rec = engine.extract(p_path).decode()
                        if rec == stress_msg:
                            st.success("✅ Recovered (100%)")
                        else:
                            st.warning("⚠️ Partial mismatch")
                    except Exception as err:
                        st.error(f"❌ Failed: {err}")
                    
                    st.image(p_path, use_container_width=True)
                    if os.path.exists(p_path): os.remove(p_path)
        finally:
            if os.path.exists(tmp_cov_path): os.remove(tmp_cov_path)
            if os.path.exists(tmp_enc_path): os.remove(tmp_enc_path)