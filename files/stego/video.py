import cv2
import numpy as np
import io
import struct
import tempfile
import os

DELIMITER = b'\x00\xFF\x00\xFF\x00\xFF\x00\xFF'

def xor_bytes(data: bytes, key: str) -> bytes:
    key_bytes = key.encode('utf-8')
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))

def bytes_to_bits(data: bytes) -> str:
    return ''.join(format(b, '08b') for b in data)

def bits_to_bytes(bits: str) -> bytes:
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

def build_payload(payload_type: str, data: bytes, filename: str = '') -> bytes:
    """
    Wrap payload with a type header so decode knows what it contains.
    Format: TYPE_TAG + 2-byte filename length + filename + data
    """
    name_encoded = filename.encode('utf-8')
    name_length = struct.pack('>H', len(name_encoded))
    tag = {
        'text':  b'TEXT__:',
        'image': b'IMAGE_:',
        'audio': b'AUDIO_:',
    }[payload_type]
    return tag + name_length + name_encoded + data

def parse_payload(raw: bytes) -> dict:
    if raw.startswith(b'TEXT__:'):
        name_len = struct.unpack('>H', raw[7:9])[0]
        content = raw[9 + name_len:]
        return {'type': 'text', 'content': content.decode('utf-8'), 'filename': ''}

    elif raw.startswith(b'IMAGE_:'):
        name_len = struct.unpack('>H', raw[7:9])[0]
        filename = raw[9:9 + name_len].decode('utf-8')
        content = raw[9 + name_len:]
        return {'type': 'image', 'content': content, 'filename': filename}

    elif raw.startswith(b'AUDIO_:'):
        name_len = struct.unpack('>H', raw[7:9])[0]
        filename = raw[9:9 + name_len].decode('utf-8')
        content = raw[9 + name_len:]
        return {'type': 'audio', 'content': content, 'filename': filename}

    else:
        raise ValueError("Unknown payload type. Wrong key or not a stego video.")


def encode_video(video_bytes: bytes, payload_type: str, payload_data: bytes,
                 key: str, filename: str = '') -> bytes:
    """
    Hide payload inside the LSB of video frames.
    Processes frames one at a time to keep memory usage flat.
    """
    # Write input video to a temp file (opencv needs a file path)
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_in:
        tmp_in.write(video_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace('.mp4', '_out.mp4')

    try:
        cap = cv2.VideoCapture(tmp_in_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file. Make sure it is a valid MP4.")

        fps    = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out    = cv2.VideoWriter(tmp_out_path, fourcc, fps, (width, height))

        # Build the full payload: encrypt, prepend size, append delimiter
        wrapped  = build_payload(payload_type, payload_data, filename)
        encrypted = xor_bytes(wrapped, key)
        size_header = struct.pack('>Q', len(encrypted))
        full_payload = size_header + encrypted + DELIMITER
        bits = bytes_to_bits(full_payload)

        # Capacity check — each frame holds width*height*3 bits (1 LSB per channel)
        bits_per_frame = width * height * 3
        total_capacity = 0
        frame_count_check = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_capacity = bits_per_frame * frame_count_check

        if len(bits) > total_capacity:
            raise ValueError("Payload is too large to fit inside this video.")

        bit_index = 0
        total_bits = len(bits)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if bit_index < total_bits:
                flat = frame.flatten().astype(np.uint8)
                bits_remaining = total_bits - bit_index
                chunk_size = min(len(flat), bits_remaining)

                for i in range(chunk_size):
                    flat[i] = (flat[i] & 0xFE) | int(bits[bit_index])
                    bit_index += 1

                frame = flat.reshape(frame.shape)

            out.write(frame)

        cap.release()
        out.release()

        with open(tmp_out_path, 'rb') as f:
            result = f.read()

        return result

    finally:
        if os.path.exists(tmp_in_path):  os.remove(tmp_in_path)
        if os.path.exists(tmp_out_path): os.remove(tmp_out_path)


def decode_video(video_bytes: bytes, key: str) -> dict:
    """
    Extract hidden payload from a stego video.
    Reads LSBs frame by frame until the full payload is recovered.
    """
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_in:
        tmp_in.write(video_bytes)
        tmp_in_path = tmp_in.name

    try:
        cap = cv2.VideoCapture(tmp_in_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file.")

        # First read 64 bits (8 bytes) to get the payload size
        size_bits = ''
        while len(size_bits) < 64:
            ret, frame = cap.read()
            if not ret:
                raise ValueError("Video too short to contain hidden data.")
            flat = frame.flatten()
            for px in flat:
                size_bits += str(int(px) & 1)
                if len(size_bits) == 64:
                    break

        payload_size = struct.unpack('>Q', bits_to_bytes(size_bits))[0]

        if payload_size > 100 * 1024 * 1024:  # 100MB sanity cap
            raise ValueError("No hidden data found or wrong key.")

        # Now read payload_size * 8 more bits
        payload_bits = ''
        total_needed = payload_size * 8

        while len(payload_bits) < total_needed:
            ret, frame = cap.read()
            if not ret:
                break
            flat = frame.flatten()
            for px in flat:
                payload_bits += str(int(px) & 1)
                if len(payload_bits) == total_needed:
                    break

        cap.release()

        if len(payload_bits) < total_needed:
            raise ValueError("Could not extract full payload — video may be corrupted.")

        payload_bytes = bits_to_bytes(payload_bits)
        decrypted = xor_bytes(payload_bytes, key)
        return parse_payload(decrypted)

    finally:
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)