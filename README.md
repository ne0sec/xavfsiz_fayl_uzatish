# 🔐 CryptoDocs — Himoyalangan Hujjat Almashish Tizimi

> **Zero-Knowledge** arxitekturasiga asoslangan, lokal tarmoqda ishlovchi xavfsiz hujjat almashish veb-tizimi.  
> Server hech qachon ochiq faylni ko'rmaydi — barcha shifrlash/deshifrlash foydalanuvchi brauzerida bajariladi.

---

## 📋 Mundarija

- [Loyiha Haqida](#-loyiha-haqida)
- [Xavfsizlik Protokollari](#-xavfsizlik-protokollari)
- [Tizim Arxitekturasi](#-tizim-arxitekturasi)
- [Talablar](#-talablar)
- [O'rnatish](#-ornatish)
- [Foydalanuvchi Rollari](#-foydalanuvchi-rollari)
- [Ishlatish](#-ishlatish)
- [Loyiha Strukturasi](#-loyiha-strukturasi)

---

## 📌 Loyiha Haqida

CryptoDocs — **client-server arxitekturasi**da qurilgan, lokal tarmoqda ishlovchi veb-tizim. Bitta kompyuter server vazifasini bajaradi, qolganlar brauzer orqali ulanadi.

### Asosiy imkoniyatlar

- 🔑 Login/parol orqali kirish — parollar **Argon2id** bilan xeshlangan
- 📤 Hujjat yuklash — **AES-256-GCM** bilan brauzerda shifrlangan holda saqlanadi
- 👥 Foydalanuvchilar o'rtasida xavfsiz ulashish
- ✅ Tasdiqlovchi orqali nazoratli ruxsat mexanizmi
- 🔀 **Shamir Secret Sharing (2-of-3)** — kalit uchta ulushga bo'linadi
- 📋 To'liq audit jurnali

---

## 🛡️ Xavfsizlik Protokollari

| Protokol | Qo'llanilgan joy | Maqsad |
|----------|-----------------|--------|
| **PBKDF2** (SHA-256, 100k iter) | Login / Ro'yxatdan o'tish | Paroldan KEK yasash |
| **AES-256-GCM** | Fayl va private key shifrlash | Autentifikatsiyali simmetrik shifrlash |
| **RSA-OAEP 2048-bit** | SSS ulushlarini qulflash | Asimmetrik shifrlash |
| **Shamir's Secret Sharing** | AES kalit taqsimlash | 2-of-3 threshold sxema |
| **Argon2id** | Parol saqlash (Django) | Brute-force himoyasi |
| **SHA-256** | Fayl yaxlitligi | Hash tekshiruvi |
| **CSRF Token** | Forma so'rovlari | Cross-site himoyasi |

### Zero-Knowledge oqimi

```
Brauzer (Client)                    Server (Django)
────────────────                    ───────────────
Parol → PBKDF2 → KEK
KEK + Private Key → AES → encrypt ──→ encrypted_private_key saqlaydi
                                        (ochiq ko'ra olmaydi)
Fayl → AES-256-GCM → .enc ────────→ .enc fayl saqlaydi
AES kalit → SSS → 3 ulush             (kalitni bilmaydi)
Ulushlar → RSA encrypt ───────────→ share_1/2/3 saqlaydi
                                        (ochiq ko'ra olmaydi)
```

---

## 🏗️ Tizim Arxitekturasi

```
┌─────────────────────────────────────────────┐
│              LOKAL TARMOQ                   │
│                                             │
│  [Server PC]          [Mijoz PC 1..N]       │
│  Django 192.168.x.x   Brauzer               │
│  SQLite               ↕ HTTP               │
│  media/ (.enc)        JavaScript (E2EE)     │
└─────────────────────────────────────────────┘
```

### Ilovalar (Django Apps)

```
accounts/   → Foydalanuvchilar, RSA kalit juftliklari, rollar
documents/  → Hujjat yuklash, tasdiqlash, deshifrlash (UI + views)
sharing/    → DocumentShare modeli (SSS ulushlarini saqlaydi)
audit/      → Barcha amallar jurnali (kim, nima, qachon)
config/     → Django sozlamalari
```

---

## ⚙️ Talablar

- Python 3.10+
- pip

```
django
cryptography
argon2-cffi
```

---

## 🚀 O'rnatish

### 1. Repozitoriyani klonlash

```bash
git clone https://github.com/USERNAME/cryptodocs.git
cd cryptodocs
```

### 2. Virtual muhit yaratish

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. `.env` fayl yaratish

Loyiha ildizida `.env` fayl yarating:

```env
SECRET_KEY=your-very-secret-key-here
DEBUG=False
ALLOWED_HOSTS=192.168.1.100,localhost,127.0.0.1
```

> ⚠️ `SECRET_KEY` uchun: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### 5. Ma'lumotlar bazasini sozlash

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Administrator yaratish

```bash
python manage.py createsuperuser
```

### 7. Serverni ishga tushirish

```bash
# Faqat lokal kompyuter uchun
python manage.py runserver

# Lokal tarmoqdagi barcha kompyuterlar uchun
python manage.py runserver 0.0.0.0:8000
```

Brauzerdan kirish: `http://192.168.x.x:8000`

---

## 👤 Foydalanuvchi Rollari

| Rol | Vazifalari |
|-----|-----------|
| **Administrator** | Foydalanuvchi yaratish, rol berish, bloklash |
| **Hujjat Egasi (Owner)** | Hujjat yuklash, qabul qiluvchi va tasdiqlovchi belgilash |
| **Qabul Qiluvchi (Receiver)** | Hujjatni deshifrlash va yuklab olish |
| **Tasdiqlovchi (Approver)** | SSS ulushini qayta shifrlash orqali ruxsat berish |

---

## 📖 Ishlatish

### To'liq jarayon

```
1. Admin → Foydalanuvchilar yaratadi (owner, receiver, approver)

2. Owner → Hujjat yuklaydi (himoyalangan)
   Brauzer: AES kalit → SSS (3 ulush) → RSA encrypt → serverga

3. Approver → Inbox ga kiradi → "Tasdiqlash" bosadi
   Brauzer: O'z ulushini RSA decrypt → Receiver kaliti bilan qayta encrypt

4. Receiver → Inbox ga kiradi → "Yuklab olish" bosadi
   Brauzer: 2 ta ulushni decrypt → AES kalit tiklanadi → fayl deshifr
```

### Shamir Demo

`/documents/sss-demo/` sahifasida:
- AES kalitini 3 ulushga bo'lish
- 2 ta ulush bilan kalitni tiklash ✅
- 1 ta ulush bilan tiklanmasligini ko'rish ❌

### Audit Jurnal

`/audit/` sahifasida barcha amallar ko'rinadi:
- Tizimga kirish / chiqish
- Hujjat yuklash
- Tasdiqlash / Rad etish
- Hujjatni ochish

---

## 📁 Loyiha Strukturasi

```
cryptodocs/
├── accounts/               # Foydalanuvchilar va autentifikatsiya
│   ├── models.py           # CustomUser (RSA kalitlar bilan)
│   ├── views.py            # Register, login, user management
│   └── templates/
│       └── registration/
│           ├── register.html   # PBKDF2 + RSA keygen (JS)
│           └── login.html      # KEK yaratish (JS)
│
├── documents/              # Asosiy funksionallik
│   ├── models.py           # Document modeli
│   ├── views.py            # Upload, approve, download views
│   ├── crypto.py           # Server-side AES yordamchi funksiyalar
│   ├── sss.py              # Shamir Secret Sharing (Python, demo)
│   └── templates/documents/
│       ├── upload.html     # E2EE fayl yuklash (JS)
│       ├── approve.html    # SSS ulushini re-encrypt (JS)
│       ├── download.html   # E2EE deshifrlash (JS)
│       ├── inbox.html      # Kiruvchi hujjatlar
│       └── sss_demo.html   # Shamir demo sahifasi
│
├── sharing/                # Hujjat almashish ruxsatnomalar
│   └── models.py           # DocumentShare (SSS ulushlarini saqlaydi)
│
├── audit/                  # Audit jurnali
│   ├── models.py           # AuditLog modeli
│   └── signals.py          # Django signallari
│
├── templates/
│   └── base.html           # Private key decrypt (JS, har sahifada)
│
├── config/
│   ├── settings.py
│   └── urls.py
│
├── .env.example            # Namuna sozlamalar
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔒 Xavfsizlik Eslatmalari

> Bu loyiha **o'quv maqsadida** yaratilgan. Haqiqiy ishlab chiqarish muhitida qo'shimcha quyidagilar tavsiya etiladi:

- **HTTPS** — `nginx` + SSL sertifikati
- **Rate limiting** — brute-force himoyasi uchun `django-ratelimit`
- **Tasodifiy PBKDF2 salt** — har foydalanuvchi uchun alohida
- **SSS ulushlarini alohida saqlash** — turli serverlar yoki xavfsiz qurilmalar
- `DEBUG = False` va `ALLOWED_HOSTS` to'g'ri sozlash

---

## 📄 Litsenziya

MIT License — o'quv va tadqiqot maqsadlarida erkin foydalanishingiz mumkin.