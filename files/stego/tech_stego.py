# Zero-width space = bit 0, Zero-width non-joiner = bit 1
ZWS  = '\u200B'  # zero-width space
ZWNJ = '\u200C'  # zero-width non-joiner
ZWSP = '\u200D'  # zero-width joiner (used as delimiter)

DELIMITER = ZWSP * 8  # 8 zero-width joiners mark end of hidden message

def text_to_bits(text: str) -> str:
    return ''.join(format(b, '08b') for b in text.encode('utf-8'))

def bits_to_text(bits: str) -> str:
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)

def encode_text_stego(cover_text: str, secret: str) -> str:
    """
    Hide secret text inside cover text using zero-width characters.
    The hidden bits are inserted between every character of the cover text.
    """
    bits = text_to_bits(secret)
    # Pad bits into zero-width characters
    hidden = ''.join(ZWS if b == '0' else ZWNJ for b in bits) + DELIMITER

    if len(cover_text) < 1:
        raise ValueError("Cover text must have at least one character.")

    # Distribute hidden characters evenly after cover text characters
    result = []
    hidden_index = 0

    for i, char in enumerate(cover_text):
        result.append(char)
        if hidden_index < len(hidden):
            result.append(hidden[hidden_index])
            hidden_index += 1

    # Append any remaining hidden chars at the end
    if hidden_index < len(hidden):
        result.append(hidden[hidden_index:])

    return ''.join(result)


def decode_text_stego(stego_text: str) -> str:
    """
    Extract hidden secret from stego text by reading zero-width characters.
    """
    bits = ''
    i = 0

    while i < len(stego_text):
        char = stego_text[i]
        if char == ZWS:
            bits += '0'
        elif char == ZWNJ:
            bits += '1'
        elif char == ZWSP:
            # Check for delimiter (8 consecutive ZWSP)
            if stego_text[i:i+8] == DELIMITER:
                break
        i += 1

    if not bits:
        raise ValueError("No hidden message found in this text.")

    try:
        return bits_to_text(bits)
    except Exception:
        raise ValueError("Could not decode hidden message. Text may be corrupted.")