def caesar_encrypt(text: str, shift: int) -> str:
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
        else:
            result.append(char)
    return ''.join(result)

def caesar_decrypt(text: str, shift: int) -> str:
    return caesar_encrypt(text, -shift)


def vigenere_encrypt(text: str, key: str) -> str:
    key = key.upper()
    result = []
    key_index = 0
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return ''.join(result)

def vigenere_decrypt(text: str, key: str) -> str:
    key = key.upper()
    result = []
    key_index = 0
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base - shift) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return ''.join(result)


def rot13_encrypt(text: str) -> str:
    return caesar_encrypt(text, 13)

def rot13_decrypt(text: str) -> str:
    return caesar_encrypt(text, 13)  # ROT13 is its own inverse


def atbash_encrypt(text: str) -> str:
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr(base + 25 - (ord(char) - base)))
        else:
            result.append(char)
    return ''.join(result)

def atbash_decrypt(text: str) -> str:
    return atbash_encrypt(text)  # Atbash is its own inverse


def rail_fence_encrypt(text: str, rails: int) -> str:
    if rails < 2:
        return text
    fence = [[] for _ in range(rails)]
    rail, direction = 0, 1
    for char in text:
        fence[rail].append(char)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    return ''.join(''.join(r) for r in fence)

def rail_fence_decrypt(text: str, rails: int) -> str:
    if rails < 2:
        return text
    n = len(text)
    pattern = []
    rail, direction = 0, 1
    for i in range(n):
        pattern.append(rail)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction

    indices = sorted(range(n), key=lambda i: pattern[i])
    result = [''] * n
    for i, char in zip(indices, text):
        result[i] = char
    return ''.join(result)


def beaufort_encrypt(text: str, key: str) -> str:
    key = key.upper()
    result = []
    key_index = 0
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((shift - (ord(char) - base)) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return ''.join(result)

def beaufort_decrypt(text: str, key: str) -> str:
    return beaufort_encrypt(text, key)  # Beaufort is its own inverse


def apply_cipher(cipher: str, text: str, mode: str, key: str = '', shift: int = 3, rails: int = 3) -> str:
    cipher = cipher.lower()
    mode = mode.lower()

    if cipher == 'caesar':
        return caesar_encrypt(text, shift) if mode == 'encrypt' else caesar_decrypt(text, shift)
    elif cipher == 'vigenere':
        if not key:
            raise ValueError("Vigenère cipher requires a key.")
        return vigenere_encrypt(text, key) if mode == 'encrypt' else vigenere_decrypt(text, key)
    elif cipher == 'rot13':
        return rot13_encrypt(text)
    elif cipher == 'atbash':
        return atbash_encrypt(text)
    elif cipher == 'railfence':
        return rail_fence_encrypt(text, rails) if mode == 'encrypt' else rail_fence_decrypt(text, rails)
    elif cipher == 'beaufort':
        if not key:
            raise ValueError("Beaufort cipher requires a key.")
        return beaufort_encrypt(text, key) if mode == 'encrypt' else beaufort_decrypt(text, key)
    else:
        raise ValueError(f"Unknown cipher: {cipher}")