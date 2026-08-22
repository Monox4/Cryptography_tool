from PIL import Image
import numpy as np
from scipy.fft import dct, idct
import io

DELIMITER = "<<END>>"

def xor_cipher(text: str, key: str) -> str:
    return "".join(
        chr(ord(c) ^ ord(key[i % len(key)]))
        for i, c in enumerate(text)
    )

def encode_dct(image_bytes: bytes, message: str, key: str) -> bytes:
    encrypted = xor_cipher(message, key) + DELIMITER
    bits = "".join(format(ord(c), "08b") for c in encrypted)

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    max_size = 1024
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    # Work on the red channel only
    r, g, b = img.split()
    r_array = np.array(r, dtype=float)

    h, w = r_array.shape
    # Pad to multiple of 8
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    r_padded = np.pad(r_array, ((0, pad_h), (0, pad_w)), mode='edge')

    bit_index = 0
    total_bits = len(bits)

    for row in range(0, r_padded.shape[0], 8):
        for col in range(0, r_padded.shape[1], 8):
            if bit_index >= total_bits:
                break
            block = r_padded[row:row+8, col:col+8]
            d = dct(dct(block.T, norm='ortho').T, norm='ortho')
            # Embed in mid-frequency coefficient (3,4)
            coef = d[3][4]
            if bits[bit_index] == '1':
                if coef >= 0:
                    d[3][4] = max(coef, 1.0)
                else:
                    d[3][4] = -max(abs(coef), 1.0)
            else:
                if coef >= 0:
                    d[3][4] = -max(abs(coef), 1.0) if abs(coef) > 0.5 else -1.0
                else:
                    d[3][4] = max(abs(coef), 1.0)
            # Make bit 1 = positive, bit 0 = negative
            d[3][4] = abs(d[3][4]) if bits[bit_index] == '1' else -abs(d[3][4])
            block_new = idct(idct(d.T, norm='ortho').T, norm='ortho')
            r_padded[row:row+8, col:col+8] = block_new
            bit_index += 1

    if bit_index < total_bits:
        raise ValueError("Message is too long to fit inside this image with DCT.")

    # Unpad and clip
    r_new = np.clip(r_padded[:h, :w], 0, 255).astype(np.uint8)
    result = Image.merge("RGB", (Image.fromarray(r_new), g, b))

    output = io.BytesIO()
    result.save(output, format="PNG")
    return output.getvalue()


def decode_dct(image_bytes: bytes, key: str) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    max_size = 1024
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    r, g, b = img.split()
    r_array = np.array(r, dtype=float)

    h, w = r_array.shape
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    r_padded = np.pad(r_array, ((0, pad_h), (0, pad_w)), mode='edge')

    bits = ""
    chars = []

    for row in range(0, r_padded.shape[0], 8):
        for col in range(0, r_padded.shape[1], 8):
            block = r_padded[row:row+8, col:col+8]
            d = dct(dct(block.T, norm='ortho').T, norm='ortho')
            coef = d[3][4]
            bits += '1' if coef >= 0 else '0'

            while len(bits) >= 8:
                byte = bits[:8]
                bits = bits[8:]
                char = chr(int(byte, 2))
                chars.append(char)
                tail = "".join(chars[-len(DELIMITER):])
                if tail == DELIMITER:
                    full_text = "".join(chars)
                    encrypted_message = full_text[:-len(DELIMITER)]
                    return xor_cipher(encrypted_message, key)

    raise ValueError("No hidden message found, or wrong key / not a stego image.")