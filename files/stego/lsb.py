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

def encode_image(image_bytes: bytes, message: str, key: str, randomize: bool = False) -> bytes:
    encrypted = xor_cipher(message, key) + DELIMITER
    bits = "".join(format(ord(c), "08b") for c in encrypted)

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    max_size = 1024
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    pixels = list(img.getdata())

    if len(bits) > len(pixels) * 3:
        raise ValueError("Message is too long to fit inside this image.")

    order = get_pixel_order(len(pixels), key, randomize)
    pixel_map = {orig: i for i, orig in enumerate(order)}

    new_pixels = list(pixels)
    bit_index = 0

    for pos in order:
        if bit_index >= len(bits):
            break
        r, g, b = pixels[pos]
        new_rgb = []
        for channel in (r, g, b):
            if bit_index < len(bits):
                new_channel = (channel & 0xFE) | int(bits[bit_index])
                bit_index += 1
            else:
                new_channel = channel
            new_rgb.append(new_channel)
        new_pixels[pos] = tuple(new_rgb)

    img.putdata(new_pixels)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def decode_image(image_bytes: bytes, key: str, randomize: bool = False) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    max_size = 1024
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    pixels = list(img.getdata())
    order = get_pixel_order(len(pixels), key, randomize)

    bits = ""
    chars = []

    for pos in order:
        for channel in pixels[pos]:
            bits += str(channel & 1)
            if len(bits) % 8 == 0:
                byte = bits[-8:]
                char = chr(int(byte, 2))
                chars.append(char)
                tail = "".join(chars[-len(DELIMITER):])
                if tail == DELIMITER:
                    full_text = "".join(chars)
                    encrypted_message = full_text[:-len(DELIMITER)]
                    return xor_cipher(encrypted_message, key)

    raise ValueError("No hidden message found, or wrong key / not a stego image.")