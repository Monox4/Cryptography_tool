import io
import struct
import numpy as np
from pydub import AudioSegment

DELIMITER = b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF'  # 8-byte binary delimiter
HEADER_SIZE = 8  # bytes to store payload size

def xor_bytes(data: bytes, key: str) -> bytes:
    key_bytes = key.encode('utf-8')
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))

def audio_to_samples(audio: AudioSegment) -> tuple:
    """Convert AudioSegment to numpy int16 array and return with metadata."""
    samples = np.array(audio.get_array_of_samples(), dtype=np.int16)
    return samples, audio.frame_rate, audio.channels, audio.sample_width

def samples_to_audio(samples: np.ndarray, frame_rate: int, channels: int, sample_width: int) -> AudioSegment:
    return AudioSegment(
        samples.tobytes(),
        frame_rate=frame_rate,
        sample_width=sample_width,
        channels=channels
    )

def load_audio(audio_bytes: bytes, fmt: str) -> AudioSegment:
    return AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)

def get_format(filename: str) -> str:
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext == 'mp3':
        return 'mp3'
    elif ext == 'flac':
        return 'flac'
    else:
        return 'wav'

def encode_audio(audio_bytes: bytes, filename: str, payload: bytes, key: str) -> tuple[bytes, str]:
    """
    Hide payload bytes inside an audio file using LSB steganography on PCM samples.
    
    Returns (encoded_audio_bytes, output_format)
    MP3 input is always returned as WAV since MP3 re-encoding is lossy.
    """
    fmt = get_format(filename)
    audio = load_audio(audio_bytes, fmt)

    # Convert to mono 16-bit for consistent processing
    audio = audio.set_sample_width(2)

    samples, rate, channels, sw = audio_to_samples(audio)

    # Build the full payload: XOR encrypt, prepend size header, append delimiter
    encrypted = xor_bytes(payload, key)
    size_header = struct.pack('>Q', len(encrypted))  # 8 bytes, big-endian uint64
    full_payload = size_header + encrypted + DELIMITER

    bits = ''.join(format(b, '08b') for b in full_payload)

    if len(bits) > len(samples):
        raise ValueError("Payload is too large to fit inside this audio file.")

    # Embed bits into LSB of each sample
    for i, bit in enumerate(bits):
        samples[i] = (int(samples[i]) & 0xFFFE) | int(bit)

    # Re-export
    out_audio = samples_to_audio(samples, rate, channels, sw)
    output = io.BytesIO()

    # MP3 → always output WAV (lossy re-encoding destroys hidden bits)
    out_fmt = 'wav' if fmt == 'mp3' else fmt
    out_audio.export(output, format=out_fmt)

    return output.getvalue(), out_fmt


def decode_audio(audio_bytes: bytes, filename: str, key: str) -> bytes:
    """
    Extract hidden payload bytes from a stego audio file.
    Returns the decrypted raw payload bytes.
    """
    fmt = get_format(filename)
    audio = load_audio(audio_bytes, fmt)
    audio = audio.set_sample_width(2)

    samples, _, _, _ = audio_to_samples(audio)

    # Read LSBs
    bits = ''.join(str(int(s) & 1) for s in samples)

    # First read the size header (8 bytes = 64 bits)
    if len(bits) < 64:
        raise ValueError("Audio file too short to contain hidden data.")

    size_bits = bits[:64]
    payload_size = struct.unpack('>Q', int(size_bits, 2).to_bytes(8, 'big'))[0]

    # Sanity check
    if payload_size > len(bits) // 8:
        raise ValueError("No hidden data found or wrong key.")

    # Read payload bits
    payload_bits = bits[64:64 + payload_size * 8]
    if len(payload_bits) < payload_size * 8:
        raise ValueError("Audio file too short to contain the full payload.")

    payload_bytes = bytes(
        int(payload_bits[i:i+8], 2)
        for i in range(0, len(payload_bits), 8)
    )

    decrypted = xor_bytes(payload_bytes, key)
    return decrypted


def encode_text_in_audio(audio_bytes: bytes, filename: str, message: str, key: str) -> tuple[bytes, str]:
    """Hide a text message inside an audio file."""
    payload = b'TEXT:' + message.encode('utf-8')
    return encode_audio(audio_bytes, filename, payload, key)


def encode_audio_in_audio(carrier_bytes: bytes, carrier_name: str,
                           hidden_bytes: bytes, hidden_name: str, key: str) -> tuple[bytes, str]:
    """Hide an audio file inside another audio file."""
    # Store the original filename so decode knows what format to reconstruct
    name_encoded = hidden_name.encode('utf-8')
    name_length = struct.pack('>H', len(name_encoded))  # 2 bytes for name length
    payload = b'AUDIO:' + name_length + name_encoded + hidden_bytes
    return encode_audio(carrier_bytes, carrier_name, payload, key)


def decode_audio_payload(audio_bytes: bytes, filename: str, key: str) -> dict:
    """
    Decode hidden payload from stego audio.
    Returns dict with 'type' ('text' or 'audio') and the content.
    """
    raw = decode_audio(audio_bytes, filename, key)

    if raw.startswith(b'TEXT:'):
        text = raw[5:].decode('utf-8')
        return {'type': 'text', 'content': text}

    elif raw.startswith(b'AUDIO:'):
        name_length = struct.unpack('>H', raw[6:8])[0]
        hidden_name = raw[8:8 + name_length].decode('utf-8')
        hidden_audio = raw[8 + name_length:]
        return {'type': 'audio', 'filename': hidden_name, 'content': hidden_audio}

    else:
        raise ValueError("Unknown payload type. Wrong key or not a stego file.")