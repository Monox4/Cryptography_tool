import io
import struct
import numpy as np
import soundfile as sf

DELIMITER = b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF'

def xor_bytes(data: bytes, key: str) -> bytes:
    key_bytes = key.encode('utf-8')
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))

def get_format(filename: str) -> str:
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext if ext in ('wav', 'flac') else 'wav'

def load_audio(audio_bytes: bytes) -> tuple:
    """Load audio bytes into numpy int16 samples."""
    buf = io.BytesIO(audio_bytes)
    data, samplerate = sf.read(buf, dtype='int16', always_2d=False)
    return data, samplerate

def save_audio(samples: np.ndarray, samplerate: int, fmt: str) -> bytes:
    """Save numpy int16 samples to bytes in given format."""
    buf = io.BytesIO()
    sf.write(buf, samples, samplerate, format=fmt.upper(), subtype='PCM_16')
    return buf.getvalue()

def encode_audio(audio_bytes: bytes, filename: str, payload: bytes, key: str) -> tuple:
    fmt = get_format(filename)

    try:
        samples, samplerate = load_audio(audio_bytes)
    except Exception as e:
        raise ValueError(f"Could not read audio file: {e}")

    # Flatten to 1D for LSB embedding
    original_shape = samples.shape
    flat = samples.flatten().astype(np.int16)

    encrypted = xor_bytes(payload, key)
    size_header = struct.pack('>Q', len(encrypted))
    full_payload = size_header + encrypted + DELIMITER
    bits = ''.join(format(b, '08b') for b in full_payload)

    if len(bits) > len(flat):
        raise ValueError("Payload is too large to fit inside this audio file.")

    for i, bit in enumerate(bits):
        flat[i] = (int(flat[i]) & 0xFFFE) | int(bit)

    result_samples = flat.reshape(original_shape)
    result_bytes = save_audio(result_samples, samplerate, fmt)
    return result_bytes, fmt


def decode_audio(audio_bytes: bytes, filename: str, key: str) -> bytes:
    try:
        samples, _ = load_audio(audio_bytes)
    except Exception as e:
        raise ValueError(f"Could not read audio file: {e}")

    flat = samples.flatten().astype(np.int16)
    bits = ''.join(str(int(s) & 1) for s in flat)

    if len(bits) < 64:
        raise ValueError("Audio file too short to contain hidden data.")

    payload_size = struct.unpack('>Q', int(bits[:64], 2).to_bytes(8, 'big'))[0]

    if payload_size > len(bits) // 8:
        raise ValueError("No hidden data found or wrong key.")

    payload_bits = bits[64:64 + payload_size * 8]
    payload_bytes = bytes(int(payload_bits[i:i+8], 2) for i in range(0, len(payload_bits), 8))
    return xor_bytes(payload_bytes, key)


def encode_text_in_audio(audio_bytes: bytes, filename: str, message: str, key: str) -> tuple:
    payload = b'TEXT:' + message.encode('utf-8')
    return encode_audio(audio_bytes, filename, payload, key)


def encode_audio_in_audio(carrier_bytes: bytes, carrier_name: str,
                           hidden_bytes: bytes, hidden_name: str, key: str) -> tuple:
    name_encoded = hidden_name.encode('utf-8')
    name_length = struct.pack('>H', len(name_encoded))
    payload = b'AUDIO:' + name_length + name_encoded + hidden_bytes
    return encode_audio(carrier_bytes, carrier_name, payload, key)


def decode_audio_payload(audio_bytes: bytes, filename: str, key: str) -> dict:
    raw = decode_audio(audio_bytes, filename, key)

    if raw.startswith(b'TEXT:'):
        return {'type': 'text', 'content': raw[5:].decode('utf-8')}
    elif raw.startswith(b'AUDIO:'):
        name_length = struct.unpack('>H', raw[6:8])[0]
        hidden_name = raw[8:8 + name_length].decode('utf-8')
        hidden_audio = raw[8 + name_length:]
        return {'type': 'audio', 'filename': hidden_name, 'content': hidden_audio}
    else:
        raise ValueError("Unknown payload type. Wrong key or not a stego file.")