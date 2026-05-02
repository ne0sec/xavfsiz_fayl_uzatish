#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Superuser avtomatik yaratish
python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
role     = os.environ.get('DJANGO_SUPERUSER_ROLE', 'admin')

if not password:
    print("OGOHLANTIRISH: DJANGO_SUPERUSER_PASSWORD sozlanmagan!")
elif not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role=role
    )
    print(f"Superuser '{username}' muvaffaqiyatli yaratildi.")
else:
    print(f"Superuser '{username}' allaqachon mavjud.")
PYEOF