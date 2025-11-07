import re

def validar_url(url: str) -> bool:
    """Valida que la URL empiece con http:// o https://"""
    return re.match(r'^https?://', url) is not None

