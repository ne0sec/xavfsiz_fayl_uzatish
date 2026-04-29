import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def calculate_sha256(file_data):
    """Faylning yaxlitligini tekshirish uchun SHA-256 xeshini hisoblaydi."""
    digest = hashlib.sha256()
    digest.update(file_data)
    return digest.hexdigest()

def encrypt_file_data(file_data):
    """
    Faylni AES-256-GCM yordamida shifrlaydi.
    Qaytaradi: (kalit, nonce, shifrlangan_matn)
    """
    # 256-bitli (32 bayt) yangi tasodifiy kalit hosil qilish
    key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(key)
    
    # GCM rejimi uchun 96-bitli (12 bayt) nonce (IV) yaratish
    nonce = os.urandom(12)
    
    # Faylni shifrlash
    ciphertext = aesgcm.encrypt(nonce, file_data, associated_data=None)
    
    return key, nonce, ciphertext