# -*- coding: utf-8 -*-
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from app.config import settings


def _get_keys(supplier_type: str = "third", mode: str = "decrypt"):
    if supplier_type == "direct":
        return settings.direct_aes_key.encode("utf-8"), settings.direct_aes_iv.encode("utf-8")
    if mode == "encrypt":
        return settings.third_upload_key.encode("utf-8"), settings.third_upload_iv.encode("utf-8")
    return settings.third_decrypt_key.encode("utf-8"), settings.third_decrypt_iv.encode("utf-8")


def encrypt_data(plain_text: str, supplier_type: str = "third") -> str:
    key, iv = _get_keys(supplier_type, mode="encrypt")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_data(cipher_text_b64: str, supplier_type: str = "third") -> str:
    key, iv = _get_keys(supplier_type, mode="decrypt")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    raw = base64.b64decode(cipher_text_b64)
    decrypted = unpad(cipher.decrypt(raw), AES.block_size)
    return decrypted.decode("utf-8")
