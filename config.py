MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "verinews"
MONGO_COLLECTION = "noticias"

USER_AGENT = (
    "VeriNewsAcademico/1.0 "
    "(proyecto escolar de recuperacion de informacion)"
)

REQUEST_TIMEOUT = 15
REQUEST_DELAY_SECONDS = 1.0
MAX_ITEMS_PER_SOURCE = 20

# Siete medios independientes.
# tipo="rss": el feed descubre las noticias.
# tipo="listing": se analiza una pagina indice para descubrir enlaces.
SOURCES = [
    {
        "nombre": "MiMorelia",
        "tipo": "rss",
        "url": "https://mimorelia.com/rss/pages/ultimas-noticias.xml",
    },
    {
        "nombre": "Aristegui Noticias",
        "tipo": "rss",
        "url": "https://editorial.aristeguinoticias.com/feed/",
    },
    {
        "nombre": "Lopez-Doriga Digital",
        "tipo": "rss",
        "url": "https://lopezdoriga.com/feed/",
    },
    {
        "nombre": "El Financiero",
        "tipo": "rss",
        "url": "https://www.elfinanciero.com.mx/rss/",
    },
    {
        "nombre": "24 Horas",
        "tipo": "rss",
        "url": "https://www.24-horas.mx/feed/",
    },
    {
        "nombre": "La Jornada",
        "tipo": "listing",
        "url": "https://www.jornada.com.mx/",
        "include_regex": (
            r"^https://www\.jornada\.com\.mx/noticia/"
            r"\d{4}/\d{2}/\d{2}/"
        ),
    },
    {
        "nombre": "Publimetro Mexico",
        "tipo": "listing",
        "url": "https://www.publimetro.com.mx/noticias/",
        "include_regex": (
            r"^https://www\.publimetro\.com\.mx/noticias/"
            r"\d{4}/\d{2}/\d{2}/"
        ),
    },
]
