from urllib.parse import urlparse

from django.core.exceptions import ValidationError

ALLOWED_DOMAINS = (
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "m.youtube.com",
)

def validate_video_url(value):
    if not value:
        return value

    try:
        parsed = urlparse(value)
    except Exception:
        raise ValidationError("Некорректный URL.")

    hostname = parsed.hostname or ""
    hostname = hostname.lower()

    # Допускаем поддомены youtube (напр. m.youtube.com) -> проверяем окончание на youtube.com или youtu.be
    allowed = any(hostname == d or hostname.endswith("." + d) for d in ALLOWED_DOMAINS)
    if not allowed:
        raise ValidationError("Разрешены ссылки только с youtube.com или youtu.be.")