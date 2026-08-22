from PIL import Image
import io

def xor_cipher(text: str, key: str) -> str:
    return "".join(
        chr(ord(c) ^ ord(key[i % len(key)]))
        for i, c in enumerate(text)
    )

DELIMITER = "<<END>>"

def encode_image(image_bytes: bytes, message: str, key: str) -> bytes:
    encrypted = xor_cipher(message, key) + DELIMITER
    bits = "".join(format(ord(c), "08b") for c in encrypted)

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = list(img.getdata())

    if len(bits) > len(pixels) * 3:
        raise ValueError("Message is too long to fit inside this image.")

    bit_index = 0
    new_pixels = []

    for pixel in pixels:
        r, g, b = pixel
        new_rgb = []
        for channel in (r, g, b):
            if bit_index < len(bits):
                new_channel = (channel & 0xFE) | int(bits[bit_index])
                bit_index += 1
            else:
                new_channel = channel
            new_rgb.append(new_channel)
        new_pixels.append(tuple(new_rgb))

    img.putdata(new_pixels)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def decode_image(image_bytes: bytes, key: str) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = list(img.getdata())

    bits = ""
    for pixel in pixels:
        for channel in pixel:
            bits += str(channel & 1)

    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))

    full_text = "".join(chars)

    if DELIMITER not in full_text:
        raise ValueError("No hidden message found, or wrong key / not a stego image.")

    encrypted_message = full_text.split(DELIMITER)[0]
    return xor_cipher(encrypted_message, key)
