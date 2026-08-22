from PIL import Image
import io
import random

def xor_cipher(text: str, key: str) -> str:
    return "".join(
        chr(ord(c) ^ ord(key[i % len(key)]))
        for i, c in enumerate(text)
    )

DELIMITER = "<<END>>"

def get_pixel_order(num_pixels: int, key: str, randomize: bool) -> list:
    indices = list(range(num_pixels))
    if randomize:
        seed = sum(ord(c) for c in key)
        random.seed(seed)
        random.shuffle(indices)
    return indices

def get_bits_per_channel(algorithm: str) -> int:
    return {"LSB-1": 1, "LSB-2": 2, "LSB-4": 4}.get(algorithm, 1)

def encode_image(image_bytes: bytes, message: str, key: str, randomize: bool = False, algorithm: str = "LSB-1", preserve_exif: bool = False) -> bytes:
    encrypted = xor_cipher(message, key) + DELIMITER
    bpc = get_bits_per_channel(algorithm)
    bits = "".join(format(ord(c), "08b") for c in encrypted)

    img = Image.open(io.BytesIO(image_bytes))

    # Extract EXIF before conversion if preserving
    exif_data = None
    if preserve_exif:
        try:
            exif_data = img.info.get("exif", None)
        except Exception:
            exif_data = None

    img = img.convert("RGB")

    max_size = 1024
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    pixels = list(img.getdata())
    capacity = len(pixels) * 3 * bpc

    if len(bits) > capacity:
        raise ValueError(f"Message is too long to fit inside this image with {algorithm}.")

    order = get_pixel_order(len(pixels), key, randomize)
    new_pixels = list(pixels)
    bit_index = 0
    mask = 0xFF ^ ((1 << bpc) - 1)

    for pos in order:
        if bit_index >= len(bits):
            break
        r, g, b = pixels[pos]
        new_rgb = []
        for channel in (r, g, b):
            if bit_index < len(bits):
                chunk = bits[bit_index:bit_index + bpc].ljust(bpc, '0')
                new_channel = (channel & mask) | int(chunk, 2)
                bit_index += bpc
            else:
                new_channel = channel
            new_rgb.append(new_channel)
        new_pixels[pos] = tuple(new_rgb)

    img.putdata(new_pixels)
    output = io.BytesIO()

    if preserve_exif and exif_data:
        img.save(output, format="PNG", exif=exif_data)
    else:
        img.save(output, format="PNG")

    return output.getvalue()


def decode_image(image_bytes: bytes, key: str, randomize: bool = False, algorithm: str = "LSB-1") -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    max_size = 1024
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    pixels = list(img.getdata())
    order = get_pixel_order(len(pixels), key, randomize)
    bpc = get_bits_per_channel(algorithm)
    mask = (1 << bpc) - 1

    bits = ""
    chars = []

    for pos in order:
        for channel in pixels[pos]:
            chunk = format(channel & mask, f'0{bpc}b')
            bits += chunk
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