import hashlib
import re
from collections import Counter


STOPWORDS = {
    "de", "la", "el", "los", "las",
    "un", "una", "unos", "unas",
    "y", "o", "en", "a", "ante",
    "con", "contra", "desde", "durante",
    "entre", "hacia", "hasta", "para",
    "por", "segun", "sin", "sobre",
    "tras", "que", "como", "se",
    "su", "sus", "es", "son",
    "fue", "han", "ha", "al", "del",
    "lo", "mas", "pero", "ya",
    "esta", "este", "estos", "estas",
    "ser", "tambien", "no", "si"
}


def hash_contenido(texto):
    return hashlib.sha256(
        (texto or "").encode("utf-8")
    ).hexdigest()


def extraer_palabras(texto):
    return re.findall(
        r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]{3,}",
        (texto or "").lower()
    )


def palabras_clave(texto, limite=10):
    tokens = [
        palabra
        for palabra in extraer_palabras(texto)
        if palabra not in STOPWORDS
        and not palabra.isdigit()
    ]

    frecuentes = Counter(
        tokens
    ).most_common(limite)

    return [
        palabra
        for palabra, frecuencia
        in frecuentes
    ]


def analizar_texto(texto):
    tokens = extraer_palabras(texto)

    return {
        "numero_palabras": len(tokens),
        "hash_contenido":
            hash_contenido(texto),
        "palabras_clave":
            palabras_clave(texto),
    }
