import os
import secrets

# 256-bitli AES kaliti uchun 257-bitli tub son (Prime number)
# P = 2^256 + 297 (bu kriptografiyada tez-tez ishlatiladigan tub son)
PRIME = 2**256 + 297

def make_shares(secret_bytes, minimum=2, shares_count=3):
    """
    AES kalitini (baytlarni) SSS bo'yicha ulushlarga bo'ladi.
    """
    # Baytlarni butun songa (integer) aylantiramiz
    secret_int = int.from_bytes(secret_bytes, byteorder='big')
    
    if secret_int >= PRIME:
        raise ValueError("Secret moduli PRIME dan kichik bo'lishi kerak.")
    
    # a_1 koeffitsiyentini tasodifiy tanlaymiz (f(x) = S + a_1*x % PRIME)
    a1 = secrets.randbelow(PRIME)
    
    shares = []
    for x in range(1, shares_count + 1):
        # y = (S + a1 * x) mod PRIME
        y = (secret_int + (a1 * x)) % PRIME
        shares.append((x, y))
        
    return shares
# documents/sss.py faylidagi recover_secret funksiyasini shunga almashtir

def recover_secret(shares, prime=PRIME):
    """
    Istalgan sondagi (t) ulushlarni qabul qilib, Lagrange interpolyatsiyasi
    orqali asl kalitni tiklaydigan universal funksiya.
    """
    secret_int = 0
    for i, (xi, yi) in enumerate(shares):
        num, den = 1, 1
        for j, (xj, yj) in enumerate(shares):
            if i != j:
                num = (num * (0 - xj)) % prime
                den = (den * (xi - xj)) % prime
                
        # Modulli bo'lish (den ning teskarisini topish)
        inverse_den = pow(den, prime - 2, prime)
        term = (yi * num * inverse_den) % prime
        secret_int = (secret_int + term) % prime
        
    return int(secret_int).to_bytes(32, byteorder='big')