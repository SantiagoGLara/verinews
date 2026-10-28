"""Preprocesamiento de texto en español para la Unidad 3 de VeriNews.

Conserva el texto original para trazabilidad y genera una representación limpia
para estadísticas y vectorización. Se usa stemming Snowball para español.
"""

import html
import re
import unicodedata

from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

# Si NLTK no puede descargar el corpus de stopwords, se utiliza esta lista
# básica para que el pipeline pueda ejecutarse también en entornos restringidos.
STOPWORDS_FALLBACK = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como",
    "con", "contra", "cual", "cuando", "de", "del", "desde", "donde",
    "durante", "e", "el", "ella", "ellas", "ello", "ellos", "en", "entre",
    "era", "erais", "eran", "eras", "eres", "es", "esa", "esas", "ese",
    "eso", "esos", "esta", "estaba", "estaban", "estado", "estamos",
    "estan", "estar", "estas", "este", "esto", "estos", "fue", "fueron",
    "ha", "habia", "habian", "han", "hasta", "hay", "la", "las", "le",
    "les", "lo", "los", "mas", "me", "mi", "mis", "mientras", "muy",
    "o", "os", "otra", "otras", "otro", "otros", "para", "pero", "poco",
    "por", "porque", "que", "quien", "quienes", "se", "sea", "ser", "si",
    "sobre", "son", "su", "sus", "tambien", "te", "tiene", "tienen",
    "todo", "todos", "tu", "tus", "un", "una", "uno", "unos", "unas",
    "y", "ya", "yo", "nos", "nosotros", "vosotros", "usted", "ustedes",
}

# La negación puede modificar el sentido de una noticia; por eso se conserva.
NEGACIONES_PRESERVADAS = {"no", "nunca", "jamás", "jamas", "sin", "ni"}
_STEMMER = SnowballStemmer("spanish")
_STOPWORDS_CACHE = None


def obtener_stopwords():
    """Obtiene stopwords en español de NLTK, con fallback si no están instaladas."""
    global _STOPWORDS_CACHE
    if _STOPWORDS_CACHE is not None:
        return _STOPWORDS_CACHE

    try:
        palabras = set(stopwords.words("spanish"))
    except LookupError:
        # El README indica cómo descargar el corpus. En entornos sin conexión
        # se utiliza una lista de respaldo, sin bloquear el procesamiento.
        palabras = set(STOPWORDS_FALLBACK)

    palabras -= NEGACIONES_PRESERVADAS
    _STOPWORDS_CACHE = palabras
    return palabras


def normalizar_texto(texto):
    """Normaliza HTML, URLs, espacios y mayúsculas sin alterar acentos españoles."""
    if not texto:
        return ""

    texto = html.unescape(str(texto))
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", " ", texto)
    texto = unicodedata.normalize("NFC", texto).lower()
    texto = re.sub(r"[\r\n\t]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def tokenizar(texto_normalizado):
    """Tokeniza con NLTK; preserve_line evita depender del modelo de frases punkt."""
    if not texto_normalizado:
        return []
    return word_tokenize(
        texto_normalizado,
        language="spanish",
        preserve_line=True,
    )


def preprocesar_texto(texto, stopwords_es=None):
    """Devuelve texto normalizado, tokens y formas derivadas para un documento."""
    if stopwords_es is None:
        stopwords_es = obtener_stopwords()

    normalizado = normalizar_texto(texto)
    tokens_originales = tokenizar(normalizado)

    # Solo palabras alfabéticas: elimina signos, números y tokens alfanuméricos.
    tokens_alfabeticos = [
        token for token in tokens_originales
        if token.isalpha() and len(token) > 1
    ]

    tokens_limpios = [
        token for token in tokens_alfabeticos
        if token not in stopwords_es
    ]
    tokens_stem = [_STEMMER.stem(token) for token in tokens_limpios]

    return {
        "texto_normalizado": normalizado,
        "tokens_originales": tokens_originales,
        "tokens_alfabeticos": tokens_alfabeticos,
        "tokens_limpios": tokens_limpios,
        "tokens_stem": tokens_stem,
        "texto_limpio": " ".join(tokens_limpios),
        "texto_stem": " ".join(tokens_stem),
    }
